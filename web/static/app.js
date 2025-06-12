// Alpine.js data for RAFT Toolkit
function raftApp() {
    return {
        activeTab: 'upload',
        isLoading: false,
        showAdvanced: false,
        uploadedFile: null,
        preview: null,
        jobs: [],
        toasts: [],
        
        // Tools-related data
        toolResults: {},
        toolsLoading: {
            eval: false,
            answer: false,
            promptflow: false,
            analysis: false,
            comparison: false,
            batch: false
        },
        
        // Tool configurations
        evalConfig: {
            model: 'gpt-4',
            workers: 4,
            inputKey: 'instruction'
        },
        
        answerConfig: {
            model: 'gpt-4',
            workers: 4,
            outputName: 'answers.jsonl'
        },
        
        promptFlowConfig: {
            type: 'chat',
            mode: 'local',
            metrics: {
                relevance: true,
                groundedness: true,
                fluency: true,
                coherence: true
            }
        },
        
        analysisConfig: {
            includeStats: true,
            includeQuality: true,
            includeDistribution: true,
            includeSamples: true,
            format: 'json'
        },
        
        comparisonConfig: {
            modelAName: 'GPT-4',
            modelBName: 'GPT-3.5',
            metrics: {
                length: true,
                speed: true,
                tokens: true
            }
        },
        
        batchConfig: {
            operation: 'evaluate',
            parallelJobs: 2
        },
        
        // Tool file handling
        evalFiles: {},
        answerFiles: {},
        promptFlowFiles: {},
        analysisFiles: {},
        comparisonFiles: {},
        batchFiles: [],
        
        config: {
            doctype: 'pdf',
            questions: 5,
            chunk_size: 512,
            distractors: 1,
            p: 1.0,
            chunking_strategy: 'semantic',
            output_format: 'hf',
            output_type: 'jsonl',
            completion_model: 'llama3.2',
            embedding_model: 'nomic-embed-text',
            system_prompt_key: 'gpt',
            workers: 1,
            embed_workers: 1,
            pace: true,
            output_chat_system_prompt: '',
            output_completion_prompt_column: 'prompt',
            output_completion_completion_column: 'completion'
        },

        init() {
            this.refreshJobs();
            // Auto-refresh jobs every 5 seconds
            setInterval(() => {
                if (this.activeTab === 'jobs') {
                    this.refreshJobs();
                }
            }, 5000);
        },

        async handleFileUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.isLoading = true;
            try {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Upload failed');

                this.uploadedFile = await response.json();
                this.showToast('File uploaded successfully!', 'success');
                
                // Auto-detect document type based on file extension
                const extension = file.name.split('.').pop().toLowerCase();
                if (['pdf', 'txt', 'json', 'pptx'].includes(extension)) {
                    this.config.doctype = extension === 'pptx' ? 'pptx' : extension;
                }
                
            } catch (error) {
                this.showToast('Upload failed: ' + error.message, 'error');
            } finally {
                this.isLoading = false;
            }
        },

        async getPreview() {
            if (!this.uploadedFile) return;

            this.isLoading = true;
            try {
                const params = new URLSearchParams({
                    file_path: this.uploadedFile.file_path,
                    doctype: this.config.doctype,
                    chunk_size: this.config.chunk_size,
                    questions: this.config.questions
                });

                const response = await fetch(`/api/preview?${params}`);
                if (!response.ok) throw new Error('Preview failed');

                this.preview = await response.json();
                this.showToast('Preview generated successfully!', 'success');
                
            } catch (error) {
                this.showToast('Preview failed: ' + error.message, 'error');
            } finally {
                this.isLoading = false;
            }
        },

        async startProcessing() {
            if (!this.uploadedFile) return;

            this.isLoading = true;
            try {
                const params = new URLSearchParams({
                    file_path: this.uploadedFile.file_path
                });

                const response = await fetch(`/api/process?${params}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.config)
                });

                if (!response.ok) throw new Error('Processing failed to start');

                const result = await response.json();
                this.showToast('Processing started successfully!', 'success');
                
                // Switch to jobs tab and refresh
                this.activeTab = 'jobs';
                this.refreshJobs();
                
            } catch (error) {
                this.showToast('Failed to start processing: ' + error.message, 'error');
            } finally {
                this.isLoading = false;
            }
        },

        async refreshJobs() {
            try {
                const response = await fetch('/api/jobs');
                if (!response.ok) throw new Error('Failed to fetch jobs');
                
                this.jobs = await response.json();
                
                // Update individual job statuses for active jobs
                for (const job of this.jobs) {
                    if (job.status === 'processing' || job.status === 'pending') {
                        this.updateJobStatus(job.job_id);
                    }
                }
                
            } catch (error) {
                console.error('Error refreshing jobs:', error);
            }
        },

        async updateJobStatus(jobId) {
            try {
                const response = await fetch(`/api/jobs/${jobId}/status`);
                if (!response.ok) return;

                const updatedJob = await response.json();
                const index = this.jobs.findIndex(job => job.job_id === jobId);
                if (index !== -1) {
                    this.jobs[index] = updatedJob;
                }
                
            } catch (error) {
                console.error('Error updating job status:', error);
            }
        },

        async downloadResult(jobId) {
            try {
                const response = await fetch(`/api/jobs/${jobId}/download`);
                if (!response.ok) throw new Error('Download failed');

                // Create download link
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `raft_dataset_${jobId.substring(0, 8)}.${this.getJobOutputType(jobId)}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                this.showToast('Download started!', 'success');
                
            } catch (error) {
                this.showToast('Download failed: ' + error.message, 'error');
            }
        },

        async deleteJob(jobId) {
            if (!confirm('Are you sure you want to delete this job?')) return;

            try {
                const response = await fetch(`/api/jobs/${jobId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) throw new Error('Delete failed');

                this.jobs = this.jobs.filter(job => job.job_id !== jobId);
                this.showToast('Job deleted successfully!', 'success');
                
            } catch (error) {
                this.showToast('Delete failed: ' + error.message, 'error');
            }
        },

        getJobOutputType(jobId) {
            // This is a simplified version - in a real app you'd store this info
            return this.config.output_type || 'jsonl';
        },

        getStatusColor(status) {
            const colors = {
                'pending': 'bg-yellow-100 text-yellow-800',
                'processing': 'bg-blue-100 text-blue-800',
                'completed': 'bg-green-100 text-green-800',
                'failed': 'bg-red-100 text-red-800'
            };
            return colors[status] || 'bg-gray-100 text-gray-800';
        },

        getStatusIcon(status) {
            const icons = {
                'pending': 'fas fa-clock',
                'processing': 'fas fa-spinner fa-spin',
                'completed': 'fas fa-check-circle',
                'failed': 'fas fa-exclamation-circle'
            };
            return icons[status] || 'fas fa-question-circle';
        },

        showToast(message, type = 'success') {
            const id = Date.now();
            const toast = { id, message, type };
            this.toasts.push(toast);

            // Remove toast after 5 seconds
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, 5000);
        },

        removeToast(id) {
            this.toasts = this.toasts.filter(t => t.id !== id);
        },

        // Tool File Upload Handlers
        handleEvalFileUpload(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.evalFiles[fileType] = file;
            }
        },

        handleAnswerFileUpload(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.answerFiles[fileType] = file;
            }
        },

        handlePromptFlowFileUpload(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.promptFlowFiles[fileType] = file;
            }
        },

        handleAnalysisFileUpload(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.analysisFiles[fileType] = file;
            }
        },

        handleComparisonFileUpload(event, fileType) {
            const file = event.target.files[0];
            if (file) {
                this.comparisonFiles[fileType] = file;
            }
        },

        handleBatchFileUpload(event) {
            const files = Array.from(event.target.files);
            this.batchFiles = files;
        },

        // Tool Execution Methods
        async runEvaluation() {
            if (!this.evalFiles.questions) {
                this.showToast('Please select a questions file', 'error');
                return;
            }

            this.toolsLoading.eval = true;
            try {
                const formData = new FormData();
                formData.append('questions_file', this.evalFiles.questions);
                formData.append('config', JSON.stringify(this.evalConfig));

                const response = await fetch('/api/tools/evaluate', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Evaluation failed');

                const result = await response.json();
                this.toolResults.eval = result;
                this.showToast('Evaluation completed successfully!', 'success');

            } catch (error) {
                this.showToast('Evaluation failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.eval = false;
            }
        },

        async generateAnswers() {
            if (!this.answerFiles.input) {
                this.showToast('Please select an input file', 'error');
                return;
            }

            this.toolsLoading.answer = true;
            try {
                const formData = new FormData();
                formData.append('input_file', this.answerFiles.input);
                formData.append('config', JSON.stringify(this.answerConfig));

                const response = await fetch('/api/tools/generate-answers', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Answer generation failed');

                const result = await response.json();
                this.toolResults.answer = result;
                this.showToast('Answer generation completed!', 'success');

            } catch (error) {
                this.showToast('Answer generation failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.answer = false;
            }
        },

        async runPromptFlowEvaluation() {
            if (!this.promptFlowFiles.dataset) {
                this.showToast('Please select a dataset file', 'error');
                return;
            }

            this.toolsLoading.promptflow = true;
            try {
                const formData = new FormData();
                formData.append('dataset_file', this.promptFlowFiles.dataset);
                formData.append('config', JSON.stringify(this.promptFlowConfig));

                const response = await fetch('/api/tools/promptflow-eval', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('PromptFlow evaluation failed');

                const result = await response.json();
                this.toolResults.promptflow = result;
                this.showToast('PromptFlow evaluation completed!', 'success');

            } catch (error) {
                this.showToast('PromptFlow evaluation failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.promptflow = false;
            }
        },

        async runDatasetAnalysis() {
            if (!this.analysisFiles.dataset) {
                this.showToast('Please select a dataset file', 'error');
                return;
            }

            this.toolsLoading.analysis = true;
            try {
                const formData = new FormData();
                formData.append('dataset_file', this.analysisFiles.dataset);
                formData.append('config', JSON.stringify(this.analysisConfig));

                const response = await fetch('/api/tools/analyze-dataset', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Dataset analysis failed');

                const result = await response.json();
                this.toolResults.analysis = result;
                this.showToast('Dataset analysis completed!', 'success');

            } catch (error) {
                this.showToast('Dataset analysis failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.analysis = false;
            }
        },

        async runModelComparison() {
            if (!this.comparisonFiles.modelA || !this.comparisonFiles.modelB) {
                this.showToast('Please select both model result files', 'error');
                return;
            }

            this.toolsLoading.comparison = true;
            try {
                const formData = new FormData();
                formData.append('model_a_file', this.comparisonFiles.modelA);
                formData.append('model_b_file', this.comparisonFiles.modelB);
                formData.append('config', JSON.stringify(this.comparisonConfig));

                const response = await fetch('/api/tools/compare-models', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Model comparison failed');

                const result = await response.json();
                this.toolResults.comparison = result;
                this.showToast('Model comparison completed!', 'success');

            } catch (error) {
                this.showToast('Model comparison failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.comparison = false;
            }
        },

        async runBatchProcessing() {
            if (this.batchFiles.length === 0) {
                this.showToast('Please select files for batch processing', 'error');
                return;
            }

            this.toolsLoading.batch = true;
            try {
                const formData = new FormData();
                this.batchFiles.forEach((file, index) => {
                    formData.append(`files`, file);
                });
                formData.append('config', JSON.stringify(this.batchConfig));

                const response = await fetch('/api/tools/batch-process', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Batch processing failed');

                const result = await response.json();
                this.toolResults.batch = result;
                this.showToast('Batch processing completed!', 'success');

            } catch (error) {
                this.showToast('Batch processing failed: ' + error.message, 'error');
            } finally {
                this.toolsLoading.batch = false;
            }
        },

        downloadToolResult(toolName, result) {
            try {
                const dataStr = JSON.stringify(result, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                
                const link = document.createElement('a');
                link.href = url;
                link.download = `${toolName}_results_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                URL.revokeObjectURL(url);
                this.showToast('Download started!', 'success');
                
            } catch (error) {
                this.showToast('Download failed: ' + error.message, 'error');
            }
        }
    }
}
#!/bin/bash

# Test Results Summary Script for GitHub Actions
# This script generates a GitHub Actions step summary and sets output variables

# Input variables (set these before calling the script)
UNIT_TESTS_STATUS="${UNIT_TESTS_STATUS:-success}"
INTEGRATION_TESTS_STATUS="${INTEGRATION_TESTS_STATUS:-success}"
API_TESTS_STATUS="${API_TESTS_STATUS:-success}"
CLI_TESTS_STATUS="${CLI_TESTS_STATUS:-success}"
DOCKER_TESTS_STATUS="${DOCKER_TESTS_STATUS:-success}"
KUBERNETES_TESTS_STATUS="${KUBERNETES_TESTS_STATUS:-}"

# Function to convert status to emoji
status_to_emoji() {
    case "$1" in
        "success") echo "✅ Passed" ;;
        "failure") echo "❌ Failed" ;;
        "skipped") echo "⏭️ Skipped" ;;
        "") echo "⏭️ Skipped" ;;
        *) echo "❓ Unknown" ;;
    esac
}

# Generate test results summary
echo "## Test Results Summary" >> $GITHUB_STEP_SUMMARY
echo "| Test Suite | Status |" >> $GITHUB_STEP_SUMMARY
echo "|------------|--------|" >> $GITHUB_STEP_SUMMARY
echo "| Unit Tests | $(status_to_emoji "$UNIT_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY
echo "| Integration Tests | $(status_to_emoji "$INTEGRATION_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY
echo "| API Tests | $(status_to_emoji "$API_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY
echo "| CLI Tests | $(status_to_emoji "$CLI_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY
echo "| Docker Tests | $(status_to_emoji "$DOCKER_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY
echo "| Kubernetes Tests | $(status_to_emoji "$KUBERNETES_TESTS_STATUS") |" >> $GITHUB_STEP_SUMMARY

# Count test results
failed_count=0
skipped_count=0
passed_count=0

check_test() {
    case "$1" in
        "success") ((passed_count++)) ;;
        "failure") ((failed_count++)) ;;
        "skipped"|"") ((skipped_count++)) ;;
    esac
}

check_test "$UNIT_TESTS_STATUS"
check_test "$INTEGRATION_TESTS_STATUS"
check_test "$API_TESTS_STATUS"
check_test "$CLI_TESTS_STATUS"
check_test "$DOCKER_TESTS_STATUS"
check_test "$KUBERNETES_TESTS_STATUS"

echo "" >> $GITHUB_STEP_SUMMARY
echo "### Summary" >> $GITHUB_STEP_SUMMARY
echo "- ✅ **Passed**: $passed_count" >> $GITHUB_STEP_SUMMARY
echo "- ❌ **Failed**: $failed_count" >> $GITHUB_STEP_SUMMARY
echo "- ⏭️ **Skipped**: $skipped_count" >> $GITHUB_STEP_SUMMARY

# Determine overall status
if [[ $failed_count -eq 0 ]]; then
    echo "tests-passed=true" >> $GITHUB_OUTPUT
    echo "" >> $GITHUB_STEP_SUMMARY
    
    if [[ $skipped_count -gt 0 ]]; then
        echo "🎉 **Core tests passed!** ($skipped_count test suite(s) skipped)" >> $GITHUB_STEP_SUMMARY
    else
        echo "🎉 **All tests passed!**" >> $GITHUB_STEP_SUMMARY
    fi
    
    exit 0
else
    echo "tests-passed=false" >> $GITHUB_OUTPUT
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "💥 **$failed_count test suite(s) failed. Please check the individual test results.**" >> $GITHUB_STEP_SUMMARY
    
    # Option to continue workflow even with some failures
    if [[ "${ALLOW_TEST_FAILURES:-false}" == "true" ]]; then
        echo "" >> $GITHUB_STEP_SUMMARY
        echo "⚠️ **Continuing workflow despite test failures** (ALLOW_TEST_FAILURES=true)" >> $GITHUB_STEP_SUMMARY
        exit 0
    else
        exit 1
    fi
fi
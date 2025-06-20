# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in the RAFT Toolkit, please report it to us responsibly.

### How to Report

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Email security concerns to: [security@raft-toolkit.com] (or use GitHub's private vulnerability reporting)
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: We'll acknowledge receipt within 48 hours
- **Initial Assessment**: We'll provide an initial assessment within 5 business days
- **Updates**: We'll keep you informed about progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

## Security Measures

### Current Security Practices

- **Dependency Scanning**: Automated dependency vulnerability scanning with Dependabot
- **Container Scanning**: Docker images scanned with Trivy for vulnerabilities
- **Code Scanning**: Static analysis with CodeQL and Bandit
- **Secrets Detection**: GitHub Advanced Security for secret scanning
- **Regular Updates**: Dependencies and base images updated regularly

### Container Security

- **Non-root User**: Containers run as non-root user `raft`
- **Minimal Base Images**: Using slim Python images with security updates
- **Layer Optimization**: Multi-stage builds to minimize attack surface
- **Security Scanning**: All images scanned before deployment

### Application Security

- **Input Validation**: All user inputs validated and sanitized
- **API Security**: Rate limiting and authentication for API endpoints
- **Secret Management**: Environment variables for sensitive configuration
- **Secure Defaults**: Security-first configuration defaults

## Known Issues and Mitigations

### Container Base Image Vulnerabilities

Some low-severity vulnerabilities in base Debian packages are filtered out as they:
- Are historical/legacy issues not applicable to containerized environments
- Require system-level updates beyond application control
- Have minimal impact in the container context

These are tracked in `.trivyignore` and reviewed regularly.

### Dependency Management

- Python dependencies are automatically updated via Dependabot
- Security patches are prioritized and applied promptly
- Development dependencies are separated from production dependencies

## Security Best Practices for Users

### Deployment Security

1. **Use Official Images**: Only use images from our official registry
2. **Keep Updated**: Regularly update to the latest version
3. **Network Security**: Use proper network isolation and firewalls
4. **Secrets Management**: Use secure secret management systems
5. **Access Control**: Implement proper authentication and authorization

### API Key Security

1. **Environment Variables**: Store API keys in environment variables
2. **Key Rotation**: Regularly rotate API keys
3. **Least Privilege**: Use keys with minimal required permissions
4. **Monitoring**: Monitor API key usage for anomalies

### Data Security

1. **Input Sanitization**: Validate all document inputs
2. **Output Review**: Review generated content before use
3. **Data Retention**: Implement appropriate data retention policies
4. **Access Logs**: Monitor access to sensitive data

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Acknowledgment sent
3. **Day 3-5**: Initial assessment and triage
4. **Day 6-30**: Investigation and fix development
5. **Day 30+**: Public disclosure (coordinated with reporter)

## Contact

For security-related questions or concerns:
- Security Email: [Create appropriate security contact]
- GitHub Security Advisories: Use private reporting feature
- General Issues: Use public GitHub issues (non-security only)

---

*This security policy is reviewed and updated regularly to reflect current best practices and threat landscape.*
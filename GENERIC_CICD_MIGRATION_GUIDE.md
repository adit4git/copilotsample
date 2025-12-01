# CI/CD Modernization Guide (Simplified – Moderate Depth)

## Purpose
Provide Copilot with a clear guideline for converting legacy .NET build/deployment processes into modern CI/CD pipelines for Java Spring Boot microservices.

## Source Patterns in Legacy .NET
- MSBuild / Visual Studio Build
- TFS/XAML pipelines
- Batch/PowerShell deployment scripts
- Manual IIS deployments
- Config transforms
- NuGet restore
- Network drive deployments

## Target Pattern for Spring Boot Microservices
### Build:
- Maven multi‑module build
- Unit & integration testing
- Static analysis (optional)

### Packaging:
- JARs
- Docker images

### Deployment:
- Kubernetes/OpenShift
- ConfigMaps/Secrets
- Rolling deployments

### Tools:
- Jenkins (preferred)
- GitHub Actions
- GitLab CI / Azure DevOps (compatible)

---

# 1. Build Pipeline Stages
1. Checkout
2. Dependency restore
3. Build modules
4. Run tests
5. Build Docker image
6. Push to registry
7. Deploy via kubectl

---

# 2. Example Jenkinsfile

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Build') {
            steps { sh 'mvn -B -DskipTests clean package' }
        }

        stage('Test') {
            steps { sh 'mvn -B test' }
        }

        stage('Docker Build') {
            steps { sh 'docker build -t myorg/order-service:${BUILD_NUMBER} .' }
        }

        stage('Push Image') {
            steps { sh 'docker push myorg/order-service:${BUILD_NUMBER}' }
        }

        stage('Deploy') {
            steps { sh 'kubectl apply -f k8s/deployment.yaml' }
        }
    }
}
```

---

# 3. Example GitHub Actions Workflow

```yaml
name: build-and-deploy

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v3
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Build
        run: mvn -B -DskipTests clean package

      - name: Test
        run: mvn -B test

      - name: Build Docker Image
        run: docker build -t ghcr.io/myorg/order-service:latest .

      - name: Push Image
        run: docker push ghcr.io/myorg/order-service:latest

      - name: Deploy
        run: kubectl apply -f k8s/deployment.yaml
```

---

# 4. Deployment Structure

```
service-name/
  Dockerfile
  k8s/
    deployment.yaml
    service.yaml
```

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 3
  selector:
    matchLabels: { app: order-service }
  template:
    metadata:
      labels: { app: order-service }
    spec:
      containers:
      - name: order-service
        image: myorg/order-service:latest
        ports:
        - containerPort: 8080
```

---

# 5. Configuration Strategy
- Use ConfigMaps for non-sensitive config.
- Use Secrets for credentials.
- Use Spring profiles via:
  - application.yml
  - application-dev.yml
  - application-prod.yml

---

# 6. CI/CD Output Required for Migration
Copilot must generate:
- Jenkinsfile or GitHub Actions workflow
- Dockerfile
- K8s deployment files
- Registry naming scheme
- Versioning strategy

---

# 7. Required Output File
Copilot should always produce:

```
analysis/output/ci_cd_recommendations.md
```

#!/bin/bash

# Build and Push Script for Unraid MCP Server
# This script builds the Docker image and pushes it to Docker Hub

set -e

# Configuration
DOCKER_USERNAME="kappy1928"
IMAGE_NAME="tower_mcpv2"
TAG="latest"

echo "🚀 Building and pushing Unraid MCP Server Docker image..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    echo "Please install Docker Desktop for Mac or Docker Engine"
    exit 1
fi

# Check if logged in to Docker Hub
if ! docker info &> /dev/null; then
    echo "❌ Not logged in to Docker Hub"
    echo "Please run: docker login -u kappy1928"
    exit 1
fi

# Build the image
echo "📦 Building Docker image..."
docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} .

# Tag for version
VERSION=$(git describe --tags --always --dirty)
if [ $? -eq 0 ]; then
    echo "🏷️  Tagging as version: ${VERSION}"
    docker tag ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG} ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
fi

# Push to Docker Hub
echo "📤 Pushing to Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}

if [ ! -z "$VERSION" ]; then
    echo "📤 Pushing version tag..."
    docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
fi

echo "✅ Successfully built and pushed Docker image!"
echo "   Image: ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
if [ ! -z "$VERSION" ]; then
    echo "   Version: ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}"
fi

echo ""
echo "🎉 Your Docker image is now available on Docker Hub!"
echo "   Pull with: docker pull ${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"
echo ""
echo "📋 For Unraid users:"
echo "   Repository: ${DOCKER_USERNAME}/${IMAGE_NAME}"
echo "   Tag: ${TAG}" 
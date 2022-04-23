IMAGE_NAME=joaocostaifg/gitlab-mirror-maker
# first characters of the current commit hash
IMAGE_TAG=$(shell git rev-parse --short HEAD)

build:
	@echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}, and tagging as latest"
	@docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
	@docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:latest"

push: build
	@echo "Pushing docker image"
	@docker push "${IMAGE_NAME}:${IMAGE_TAG}"
	@docker push "${IMAGE_NAME}:latest"

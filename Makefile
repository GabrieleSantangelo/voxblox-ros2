ROS_DISTRO := jazzy

CONTAINER_IMAGE := voxblox:$(ROS_DISTRO)
CONTAINER_NAME := voxblox_$(ROS_DISTRO)


PERCENT := %
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

default: help


build: ## Build release container
	@echo "Building $(CONTAINER_ROS) container image..."
	@docker build \
		--tag $(CONTAINER_IMAGE) \
		--file docker/Dockerfile.base \
		--build-arg ROS_DISTRO=$(ROS_DISTRO) \
		.

run: ## Run container in development mode
	@echo "Running $(CONTAINER_IMAGE) container in development mode..."
	@xhost +
	@docker run \
		--interactive \
		--tty \
		--rm \
		--runtime nvidia \
		--gpus all \
		--privileged \
		--net host \
		--ipc host \
		--name ${CONTAINER_NAME}-dev \
		--volume /tmp/.X11-unix:/tmp/.X11-unix \
		--volume ~/.Xauthority:/root/.Xauthority \
		--env DISPLAY=$$DISPLAY \
		--env XAUTHORITY=$$XAUTHORITY \
		--volume $(ROOT_DIR)/entrypoint.sh:/workspace/entrypoint.sh \
		--volume $(ROOT_DIR):/workspace/src/ \
		$(CONTAINER_IMAGE) \
		bash 

enter: ## Enter running container in development mode
	@echo "Entering $(CONTAINER_IMAGE) container..."
	@docker exec -it ${CONTAINER_NAME}-dev bash

clean: ## Clean up container image
	@echo "Cleaning up $(CONTAINER_IMAGE) container image..."
	@docker rmi $(CONTAINER_IMAGE) || true

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: build run-dev enter-dev clean help



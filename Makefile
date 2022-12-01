SHELL := /bin/bash

# all monitor components share/use the following targets/exports
DOCKER_HOST = $(shell echo $$DOCKER_HOST)
BUILD_TAG ?= git-$(shell git rev-parse --short HEAD)
DRYCC_REGISTRY ?= ${DEV_REGISTRY}
IMAGE_PREFIX ?= drycc
PLATFORM ?= linux/amd64,linux/arm64

include versioning.mk

TEST_ENV_PREFIX := docker run --rm -v ${CURDIR}:/bash -w /bash ${DEV_REGISTRY}/drycc/python-dev

build: docker-build
push: docker-push
deploy: docker-build docker-push install

check-docker:
	@if [ -z $$(which docker) ]; then \
		echo "Missing \`docker\` client which is required for development"; \
		exit 2; \
	fi

docker-build:
	docker build ${DOCKER_BUILD_FLAGS} -t ${IMAGE} .
	docker tag ${IMAGE} ${MUTABLE_IMAGE}

docker-buildx:
	docker buildx build --platform ${PLATFORM} -t ${IMAGE} . --push

clean: check-docker
	docker rmi $(IMAGE)
	
test: test-style

test-style:
	${TEST_ENV_PREFIX} bash -c "set -eou pipefail; flake8 --exclude .venv --show-source"

.PHONY: build push docker-build clean upgrade deploy test test-style

build-all:
	docker build ${DOCKER_BUILD_FLAGS} -t ${DRYCC_REGISTRY}/${IMAGE_PREFIX}/prometheus:${VERSION}

push-all:
	docker push ${DRYCC_REGISTRY}/${IMAGE_PREFIX}/prometheus:${VERSION}

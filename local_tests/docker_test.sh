#!/bin/bash
docker buildx build  -t test:latest .
docker run -d test

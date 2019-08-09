#!/bin/sh
exec docker build -t lead:latest -f ./Dockerfile ..

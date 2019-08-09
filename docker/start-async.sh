#!/bin/sh
exec docker run -d --network=host lead >process.txt

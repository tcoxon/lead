#!/bin/sh
exec docker stop $(cat process.txt)

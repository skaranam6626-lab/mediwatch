#!/bin/bash
set -e
echo "📥 Downloading Mediwatch dataset..."


if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "HOME_PATH:$HOME_PATH"
cd $HOME_PATH
mkdir -p ./input ./output
curl -L -o ./input/diabetes.zip https://www.kaggle.com/api/v1/datasets/download/brandao/diabetes
unzip -o ./input/diabetes.zip -d ./input
echo "Data ready"
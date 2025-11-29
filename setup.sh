#!/bin/bash
# setup.sh
chmod +x mdex.py
mkdir -p ~/bin
cp mdex.py ~/bin/mdex
echo 'export PATH="$HOME/bin:$PATH"' >>~/.zshrc # or ~/.bashrc
source ~/.zshrc                                 # or ~/.bashrc
echo "✅ mdex is ready! Run: mdex <filename>.mdex"

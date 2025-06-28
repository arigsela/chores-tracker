#!/bin/bash
# Temporary fix for ip.txt sandbox issue

# Find and comment out the ip.txt write
find "$HOME/Library/Developer/Xcode/DerivedData" -name "react-native-xcode.sh" -exec sed -i '' 's/echo.*ip.txt/# &/g' {} \;

echo "Build fix applied. Try building again."
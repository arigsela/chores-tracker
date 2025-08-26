#!/bin/bash
# Debug script to understand MySQL user creation issues

echo "🔍 Debugging MySQL user setup..."

# Check if MySQL pod is running
kubectl get pods -n chores-dev -l app=mysql

echo -e "\n📋 MySQL pod logs (last 20 lines):"
kubectl logs -n chores-dev -l app=mysql --tail=20

echo -e "\n🔧 Testing root connection..."
kubectl exec -n chores-dev deployment/mysql -- mysql -u root -prootpassword -e "SELECT User, Host FROM mysql.user;" 2>/dev/null || echo "❌ Root connection failed"

echo -e "\n👤 Checking if chores_user exists..."
kubectl exec -n chores-dev deployment/mysql -- mysql -u root -prootpassword -e "SELECT User, Host FROM mysql.user WHERE User='chores_user';" 2>/dev/null || echo "❌ Can't query users table"

echo -e "\n🏗️  Checking if chores_db database exists..."
kubectl exec -n chores-dev deployment/mysql -- mysql -u root -prootpassword -e "SHOW DATABASES;" 2>/dev/null || echo "❌ Can't show databases"

echo -e "\n🔑 Testing chores_user connection directly..."
kubectl exec -n chores-dev deployment/mysql -- mysql -u chores_user -pchores_pass -e "SELECT 1;" 2>/dev/null && echo "✅ chores_user connection works!" || echo "❌ chores_user connection failed"
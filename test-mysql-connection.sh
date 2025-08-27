#!/bin/bash
# Quick test script to verify MySQL connection from backend

echo "Testing MySQL connection..."

# Wait for MySQL pod to be ready
echo "Waiting for MySQL pod to be ready..."
kubectl wait --for=condition=ready pod -l app=mysql -n chores-dev --timeout=120s

# Test connection from a temporary pod
echo "Testing connection with mysql client..."
kubectl run mysql-test --rm -i --restart=Never --image=mysql:5.7 -n chores-dev -- \
  mysql -h mysql.chores-dev.svc.cluster.local -u chores_user -pchores_pass -D chores_db -e "SELECT 1 as test_connection;"

if [ $? -eq 0 ]; then
    echo "✅ MySQL connection successful!"
else
    echo "❌ MySQL connection failed!"
    echo "Checking MySQL logs..."
    kubectl logs -l app=mysql -n chores-dev --tail=20
fi
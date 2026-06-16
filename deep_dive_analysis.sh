#!/bin/bash
# Deep dive analysis script

echo "=========================================="
echo "1. TEST COVERAGE PER MICROSERVICE"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
for d in */app/; do
  svc=$(echo $d | cut -d/ -f1)
  # skip symlinks (sales_assistant -> sales-assistant, sales_coach -> sales-coach)
  if [ -L "$svc" ]; then continue; fi
  if [ -d "${d}tests" ]; then
    count=$(find "${d}tests" -name '*.py' 2>/dev/null | wc -l)
    echo "$svc: $count test files"
  else
    echo "$svc: NO TESTS DIRECTORY"
  fi
done

echo ""
echo "=========================================="
echo "2. CLOUD SERVICE FILES WITH NO CORRESPONDING TEST"
echo "=========================================="
# Build list of test file stems (remove test_ prefix and .py suffix)
cd /home/hermes/one-cloud-four-ends/cloud/app/tests
declare -A test_stems
for tf in *.py; do
  stem=$(echo "$tf" | sed 's/^test_//' | sed 's/\.py$//')
  test_stems["$stem"]=1
done

# Check each service file
cd /home/hermes/one-cloud-four-ends/cloud/app/services
untested=0
tested=0
for sf in *.py; do
  # Skip __init__.py
  if [ "$sf" = "__init__.py" ]; then continue; fi
  stem=$(echo "$sf" | sed 's/\.py$//')
  if [ -z "${test_stems[$stem]}" ]; then
    echo "NO TEST: cloud/app/services/$sf"
    untested=$((untested + 1))
  else
    tested=$((tested + 1))
  fi
done
echo "Total untested service files: $untested / $((untested + tested))"

echo ""
echo "=========================================="
echo "3. CIRCULAR IMPORT RISK — cross-service references in cloud/app/services/"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends/cloud/app/services
for sf in *.py; do
  while IFS= read -r line; do
    # Match imports from other files in the same services directory
    if echo "$line" | grep -qE "from cloud\.app\.services\.|from \.\.services\.|from \.services\.|import cloud\.app\.services\."; then
      # Extract what they import
      imported=$(echo "$line" | grep -oP '(?:from|import)\s+(?:cloud\.app\.services\.|\.\.services\.|\.services\.)?\K[a-zA-Z_]+' | head -1)
      if [ -n "$imported" ] && [ "$imported" != "__init__" ]; then
        # Check if it's a circular pattern by looking for two-way references
        if echo "$line" | grep -qE "\.(memory_service|agent_core|compliance_service|mdt_engine_service|brain_orchestrator_service|sage_engine_service)"; then
          echo "CIRCULAR-RISK in $sf: $line"
        fi
      fi
    fi
  done < "$sf"
done

echo ""
echo "=========================================="
echo "4. DEAD MODULES — files never imported anywhere"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
# Only check non-test, non-init files
find cloud/app -name '*.py' -not -path '*/tests/*' -not -name '__init__.py' -not -path '*/migrations/*' | while read f; do
  # Get module path relative to project
  relpath="${f#./}"
  # Build dotted module path
  module_path=$(echo "$relpath" | sed 's/\.py$//' | tr '/' '.')
  # Check if this module is imported anywhere in the project (excluding the file itself)
  count=$(grep -rl "$module_path" --include='*.py' . 2>/dev/null | grep -v "$f" | wc -l)
  if [ "$count" -eq 0 ]; then
    echo "DEAD: $relpath"
  fi
done

echo ""
echo "=========================================="
echo "5. DUPLICATED UTILITY CLASSES (shared/ vs local)"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
# Look for classes defined in shared/
grep -rn "^class " shared/ --include='*.py' | grep -v __init__ | while IFS= read -r shared_class; do
  class_name=$(echo "$shared_class" | grep -oP 'class \K[a-zA-Z_]+')
  # Check if the same class name appears in microservice app/ dirs (non-test, non-shared)
  found_in=$(grep -rl "^class $class_name" --include='*.py' cloud/app/ assistants/app/ clinical-ops/app/ management/app/ market-access/app/ opportunity/app/ patient-engage/app/ pharma_intel/app/ sales-assistant/app/ sales-coach/app/ agents/ web/ 2>/dev/null | grep -v __init__ | grep -v tests/ | head -5)
  if [ -n "$found_in" ]; then
    echo "DUPLICATE CLASS '$class_name': defined in $shared_class ALSO in:"
    echo "$found_in" | sed 's/^/  /'
  fi
done

echo ""
echo "=========================================="
echo "6. agent_runtime/ MODULE COUNT"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
if [ -d "cloud/app/agent_runtime" ]; then
  find cloud/app/agent_runtime -name '*.py' | sort
  echo "Total files: $(find cloud/app/agent_runtime -name '*.py' | wc -l)"
  echo "Total lines: $(find cloud/app/agent_runtime -name '*.py' -exec cat {} + | wc -l)"
else
  echo "cloud/app/agent_runtime/ does not exist"
fi

echo ""
echo "=========================================="
echo "7. SILENT EXCEPTION SWALLOWING (except: pass)"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
grep -rn "except.*:" --include='*.py' cloud/app/ agents/ shared/ assistants/ clinical-ops/ management/ market-access/ opportunity/ patient-engage/ pharma_intel/ sales-assistant/ sales-coach/ 2>/dev/null | grep -v tests/ | grep -v __pycache__ | while IFS=: read -r file lineno line; do
  # Check if the next line(s) after 'except' contains only 'pass'
  line_before=$(echo "$line" | sed 's/except.*://')
  if [ -z "$line_before" ]; then
    # Check the line after
    next_line=$(sed -n "$((lineno+1))p" "$file" 2>/dev/null)
    if echo "$next_line" | grep -q "^\s*pass\s*$"; then
      echo "SILENT_SWALLOW in $file:$lineno: $line -> $next_line"
    fi
  fi
done

echo ""
echo "=========================================="
echo "8. LONG METHODS (>50 lines) in production .py files"
echo "=========================================="
cd /home/hermes/one-cloud-four-ends
find cloud/app agents shared -name '*.py' -not -path '*/tests/*' -not -path '*/migrations/*' -not -name '__init__.py' 2>/dev/null | while read f; do
  awk '
  /^def |^async def / { 
    if (name != "" && line_count > 50) {
      printf "LONG_METHOD(%d lines): %s -> %s\n", line_count, file, name
    }
    name=$0; line_count=0; next
  }
  /^class / { 
    if (name != "" && line_count > 50) {
      printf "LONG_METHOD(%d lines): %s -> %s\n", line_count, file, name
    }
    name=""; line_count=0; next
  }
  { if (name != "") line_count++ }
  END { 
    if (name != "" && line_count > 50) {
      printf "LONG_METHOD(%d lines): %s -> %s\n", line_count, file, name
    }
  }
  ' file="$f" 
done

echo ""
echo "DONE"

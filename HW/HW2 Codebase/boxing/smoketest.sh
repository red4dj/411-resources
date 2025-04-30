#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://127.0.0.1:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
  echo ""  # Add blank line in output
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"status": "success"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
  echo ""  # Add blank line in output
}


##########################################################
#
# Boxer Management
#
##########################################################

create_boxer() {
  name=$1
  weight=$2
  height=$3
  reach=$4
  age=$5

  echo "Creating boxer ($name, $weight, $height, $reach, $age)..."
  curl -s -X POST "$BASE_URL/add-boxer" -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\", \"weight\":$weight, \"height\":$height, \"reach\":$reach, \"age\":$age}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Boxer created successfully."
  else
    echo "Failed to create boxer."
  fi
  echo ""  # Add blank line in output
}

delete_boxer() {
  boxer_id=$1

  echo "Deleting boxer by ID ($boxer_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-boxer/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer deleted successfully by ID ($boxer_id)."
  else
    echo "Failed to delete boxer by ID ($boxer_id)."
  fi
  echo ""  # Add blank line in output
}

get_boxer_by_id() {
  boxer_id=$1

  echo "Getting boxer by ID ($boxer_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-id/$boxer_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by ID ($boxer_id)."
  else
    echo "Failed to get boxer by ID ($boxer_id)."
  fi

  if [ "$ECHO_JSON" = true ]; then
    echo "Boxer JSON (ID $boxer_id):"
    echo "$response" | jq .
  fi
  echo ""  # Add blank line in output
}

get_boxer_by_name() {
  boxer_name=$1

  echo "Getting boxer by name ($boxer_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-boxer-by-name/$(echo $boxer_name | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Boxer retrieved successfully by name."
  else
    echo "Failed to get boxer by name."
  fi

  if [ "$ECHO_JSON" = true ]; then
    echo "Boxer JSON (Name $boxer_name):"
    echo "$response" | jq .
  fi
  echo ""  # Add blank line in output
}

get_leaderboard() {
  sort=$1

  echo "Getting leaderboard sorted by $sort..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard?sort=$sort")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
  else
    echo "Failed to get leaderboard."
  fi

  if [ "$ECHO_JSON" = true ]; then
    echo "Leaderboard JSON:"
    echo "$response" | jq .
  fi
  echo ""  # Add blank line in output
}


############################################################
#
# Ring Management
#
############################################################

#Error handling and additional test cases.
enter_ring() {
  name=$1

  echo "Let $name into the ring..."
  response=$(curl -s -X POST "$BASE_URL/enter-ring" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\"}")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "$name entered the ring."
  else
    echo "Failed to enter $name. Error:"
    echo "$response" | jq .
  fi

  echo ""  # Add blank line in output
}

fight() {
  echo "Fight..."

  response=$(curl -s -X GET "$BASE_URL/fight")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Fight complete."
    if [ "$ECHO_JSON" = true ]; then
      echo "Fight JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Fight failed (expected if < 2 boxers)."
    echo "$response" | jq .
  fi

  echo ""  # Add blank line in output
}

clear_ring() {
  echo "Clear the ring..."
  response=$(curl -s -X POST "$BASE_URL/clear-boxers")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Ring cleared."
  else
    echo "Failed to clear the ring."
    echo "$response" | jq .
  fi
  echo ""  # Add blank line in output
}

get_boxers_in_ring() {
  echo "Fetching boxers currently in the ring..."
  response=$(curl -s "$BASE_URL/get-boxers")
  echo "$response" | jq .
  echo ""  # Add blank line in output
}



############################################################
#
# Run Tests
#
############################################################

# Initialize the database
#sqlite3 data/boxing.db < sql/init_db.sql

# Health checks
check_health
check_db

# Run Smoketests
create_boxer "John Doe" 160 66 24 21
create_boxer "Jane Doe" 150 63 22 20
create_boxer "Judy Doe" 140 60 20 19
echo "Expect failure (Cannot add 2 boxers with same name):"
create_boxer "John Doe" 160 66 24 21

delete_boxer 3

create_boxer "Judy Doe" 140 60 20 19

get_boxer_by_id 1
get_boxer_by_id 2
get_boxer_by_id 4

get_boxer_by_name "John Doe"
get_boxer_by_name "Jane Doe"
get_boxer_by_name "Judy Doe"

get_leaderboard "wins"
get_leaderboard "win_pct"

clear_ring
enter_ring "John Doe"
echo "Expect failure (Only one boxer in ring):"
fight  # Expect fail
clear_ring

enter_ring "John Doe"
enter_ring "Judy Doe"
echo "Expect failure (Only two boxers allowed in ring):"
enter_ring "Jane Doe"  # This should NOT be allowed because>2 boxer

#reset
clear_ring

#entering a boxer who doesn’t exist in the database
echo "Expect failure (Cannot add boxer who doesn't exist):"
enter_ring "Zoe"  # Should fail

#noral fight
enter_ring "John Doe"
enter_ring "Judy Doe"
fight

#Final clean-up
clear_ring


echo "All tests passed successfully!"
---

backend:
  - task: "Component-Unit Relationship API"
    implemented: true
    working: "needs_testing"
    file: "/app/backend/routers/relationships.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

frontend:
  - task: "Component Relationship View Component"
    implemented: true
    working: "needs_testing"
    file: "/app/frontend/src/components/ComponentRelationshipView.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

  - task: "Barcode Scanner Component"
    implemented: true
    working: "needs_testing"
    file: "/app/frontend/src/components/BarcodeScanner.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

  - task: "Drag-Drop Storage Transfer"
    implemented: true
    working: "needs_testing"
    file: "/app/frontend/src/pages/InventoryEnhanced.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: true

metadata:
  created_by: "main_agent"
  version: "1.5"
  test_sequence: 5
  run_ui: true

test_plan:
  current_focus:
    - "Component-Unit Relationship View"
    - "Barcode Scanner"
    - "Drag-Drop functionality"
  stuck_tasks: []
  test_all: true
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Implemented Component-Unit Relationship View showing visual tree of parent blood unit and derived components. Added Barcode Scanner with html5-qrcode library supporting single and bulk scan modes. Added drag-drop functionality using @dnd-kit library for moving items between storage locations. The Relationship View is accessible from search results and storage contents table via a GitBranch icon button."

test_credentials:
  admin:
    email: "admin@bloodbank.com"
    password: "adminpassword"

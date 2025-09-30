import { test, expect } from '@playwright/test'

// Test configuration
const baseURL = process.env.BASE_URL || 'http://localhost:8080'
const testConfig = {
  username: process.env.TEST_USERNAME || 'test@example.com',
  password: process.env.TEST_PASSWORD || 'password',
  courseName: process.env.TEST_COURSE || 'Compliance Training 2024'
}

test.describe('Document Workflow Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to LMS app
    await page.goto(`${baseURL}/lms`)

    // Login if not already logged in
    try {
      await page.waitForSelector('[data-testid="login-form"]', { timeout: 3000 })
      await page.fill('input[type="email"]', testConfig.username)
      await page.fill('input[type="password"]', testConfig.password)
      await page.click('button[type="submit"]')
      await page.waitForNavigation()
    } catch (error) {
      // Already logged in or different login structure
      console.log('Login form not found, assuming already logged in')
    }
  })

  test.describe('Step Indicator Component', () => {
    test('should display step indicator with correct steps', async ({ page }) => {
      // Navigate to a course that triggers document workflow
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Complete course to trigger document modal (mock API response)
      await page.evaluate(() => {
        window.postMessage({
          type: 'COURSE_COMPLETED',
          courseName: 'Compliance Training 2024'
        }, '*')
      })

      // Wait for document modal to appear
      await page.waitForSelector('[data-testid="document-wizard-modal"]', { timeout: 10000 })

      // Check step indicator is present
      await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible()

      // Verify all 4 steps are present
      const steps = page.locator('[data-testid="step-circle"]')
      await expect(steps).toHaveCount(4)

      // Verify step labels
      await expect(page.locator('text=Certify')).toBeVisible()
      await expect(page.locator('text=Download')).toBeVisible()
      await expect(page.locator('text=Upload')).toBeVisible()
      await expect(page.locator('text=Complete')).toBeVisible()

      // Verify first step is active
      await expect(page.locator('[data-testid="step-circle"]:first-child')).toHaveClass(/bg-white.*border-gray-900/)
    })

    test('should update progress percentage correctly', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Trigger document workflow
      await page.evaluate(() => {
        window.postMessage({
          type: 'COURSE_COMPLETED',
          courseName: 'Compliance Training 2024'
        }, '*')
      })

      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Check initial progress is 25% (step 1 of 4)
      await expect(page.locator('text=25% Complete')).toBeVisible()

      // Move to next step and verify progress updates
      await page.click('[data-testid="next-button"]')
      await expect(page.locator('text=50% Complete')).toBeVisible()
    })

    test('should allow navigation to completed steps', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Mock workflow state with completed steps
      await page.evaluate(() => {
        // Set up mock state where first step is completed
        window.mockWorkflowState = {
          currentStep: 2,
          certification: { isCompleted: true }
        }
      })

      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Click on first step (should be clickable since it's completed)
      await page.click('[data-testid="step-circle"]:first-child')

      // Verify we're back on step 1
      await expect(page.locator('[data-testid="certification-step"]')).toBeVisible()
    })
  })

  test.describe('Certification Step', () => {
    test('should display distributor declaration form', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Mock distributor role
      await page.evaluate(() => {
        window.mockUserRole = 'Distributor'
        window.mockDeclarationInfo = {
          distributor_company_name: 'Test Distributor Inc',
          attendee_name: 'John Doe',
          designation: 'Compliance Officer'
        }
      })

      await page.waitForSelector('[data-testid="certification-step"]')

      // Verify distributor-specific content
      await expect(page.locator('text=Meril Distributor - Compliance Policy Adoption Form')).toBeVisible()
      await expect(page.locator('text=Test Distributor Inc')).toBeVisible()

      // Verify form fields
      await expect(page.locator('input[id="certification-name"]')).toBeVisible()
      await expect(page.locator('input[id="certification-date"]')).toBeVisible()
      await expect(page.locator('button:has-text("I Certify")')).toBeVisible()
    })

    test('should display employee declaration form', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Mock employee role
      await page.evaluate(() => {
        window.mockUserRole = 'Employee'
        window.mockDeclarationInfo = {
          employee_name: 'Jane Smith',
          custom_employee_id: 'EMP001',
          company: 'Meril Life Sciences'
        }
      })

      await page.waitForSelector('[data-testid="certification-step"]')

      // Verify employee-specific content
      await expect(page.locator('text=Employee Declaration - Ethical Practices & Compliance')).toBeVisible()
      await expect(page.locator('text=Jane Smith')).toBeVisible()
      await expect(page.locator('text=EMP001')).toBeVisible()
    })

    test('should validate certification form', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="certification-step"]')

      // Try to submit without name
      await page.click('button:has-text("I Certify")')

      // Should show validation error
      await expect(page.locator('text=Name must be at least 3 characters long')).toBeVisible()

      // Fill name with less than 3 characters
      await page.fill('input[id="certification-name"]', 'Jo')
      await page.click('button:has-text("I Certify")')

      // Should still show validation error
      await expect(page.locator('text=Name must be at least 3 characters long')).toBeVisible()

      // Fill valid name
      await page.fill('input[id="certification-name"]', 'John Doe')
      await page.click('button:has-text("I Certify")')

      // Should proceed to next step
      await expect(page.locator('[data-testid="download-step"]')).toBeVisible()
    })
  })

  test.describe('Download Step', () => {
    test('should display required documents for download', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Navigate to download step
      await page.evaluate(() => {
        window.mockWorkflowState = {
          currentStep: 2,
          certification: { isCompleted: true },
          requiredDocuments: [
            { name: 'Meril Distributor Compliance Policy Adoption Form' },
            { name: 'Distributor Self Declaration' },
            { name: 'Meril Distributor Compliance Code of Conduct' }
          ]
        }
      })

      await page.waitForSelector('[data-testid="download-step"]')

      // Verify instructions
      await expect(page.locator('text=Download the generated documents')).toBeVisible()
      await expect(page.locator('text=Insert your company\'s letterhead')).toBeVisible()

      // Verify document list
      await expect(page.locator('text=Meril Distributor Compliance Policy Adoption Form')).toBeVisible()
      await expect(page.locator('text=Distributor Self Declaration')).toBeVisible()
      await expect(page.locator('text=Meril Distributor Compliance Code of Conduct')).toBeVisible()

      // Verify download buttons
      const downloadButtons = page.locator('button:has-text("Download")')
      await expect(downloadButtons).toHaveCount(3)
    })

    test('should handle document download', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="download-step"]')

      // Mock download response
      await page.route('**/api/method/lms.overrides.documents.generate_dynamic_docx', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            file_content: 'base64content',
            file_name: 'test_document.pdf'
          })
        })
      })

      // Click download button
      await page.click('button:has-text("Download"):first')

      // Verify loading state
      await expect(page.locator('svg[data-testid="spinner"]')).toBeVisible()

      // Wait for download to complete
      await page.waitForTimeout(2000)

      // Verify success state
      await expect(page.locator('text=Downloaded')).toBeVisible()
    })

    test('should track download progress', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="download-step"]')

      // Initially should show 0 downloads
      await expect(page.locator('text=0 of 3 documents downloaded')).toBeVisible()
      await expect(page.locator('[data-testid="download-progress-bar"]')).toHaveCSS('width', '0%')

      // Mock successful download
      await page.evaluate(() => {
        window.markDownloadCompleted('Meril Distributor Compliance Policy Adoption Form')
      })

      // Should update progress
      await expect(page.locator('text=1 of 3 documents downloaded')).toBeVisible()
      await expect(page.locator('text=33%')).toBeVisible()
    })
  })

  test.describe('Upload Step', () => {
    test('should display upload interface', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Navigate to upload step
      await page.evaluate(() => {
        window.mockWorkflowState = {
          currentStep: 3,
          currentDocument: { name: 'Meril Distributor Compliance Policy Adoption Form' },
          requiredDocuments: [
            { name: 'Meril Distributor Compliance Policy Adoption Form' },
            { name: 'Distributor Self Declaration' },
            { name: 'Meril Distributor Compliance Code of Conduct' }
          ]
        }
      })

      await page.waitForSelector('[data-testid="upload-step"]')

      // Verify upload interface
      await expect(page.locator('text=Upload your signed and completed documents')).toBeVisible()
      await expect(page.locator('input[type="file"]')).toBeVisible()
      await expect(page.locator('text=Supported formats: .docx, .doc, .pdf')).toBeVisible()
      await expect(page.locator('button:has-text("Upload Document")')).toBeVisible()
    })

    test('should validate file upload', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="upload-step"]')

      // Try to upload without selecting file
      await page.click('button:has-text("Upload Document")')
      await expect(page.locator('text=Please select a file')).toBeVisible()

      // Test file size validation (mock large file)
      await page.evaluate(() => {
        const fileInput = document.querySelector('input[type="file"]')
        const largefile = new File(['x'.repeat(5 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' })

        const event = new Event('change', { bubbles: true })
        Object.defineProperty(fileInput, 'files', {
          value: [largefile],
          configurable: true
        })
        fileInput.dispatchEvent(event)
      })

      await expect(page.locator('text=File size must be less than 4MB')).toBeVisible()
    })

    test('should handle successful file upload', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="upload-step"]')

      // Mock upload API
      await page.route('**/api/method/lms.overrides.documents.upload_distributor_document_with_datetime', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Document uploaded successfully'
          })
        })
      })

      // Simulate file selection
      const fileContent = 'This is a test PDF content'
      await page.setInputFiles('input[type="file"]', {
        name: 'test-document.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from(fileContent)
      })

      // Submit upload
      await page.click('button:has-text("Upload Document")')

      // Verify upload progress
      await expect(page.locator('text=Uploading...')).toBeVisible()
      await expect(page.locator('[data-testid="upload-progress-bar"]')).toBeVisible()

      // Wait for upload completion
      await expect(page.locator('text=Document uploaded successfully')).toBeVisible()
    })

    test('should show upload progress for multiple documents', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="upload-step"]')

      // Mock multiple documents scenario
      await page.evaluate(() => {
        window.mockWorkflowState = {
          uploadedDocuments: new Set(['Distributor Self Declaration']),
          requiredDocuments: [
            { name: 'Meril Distributor Compliance Policy Adoption Form' },
            { name: 'Distributor Self Declaration' },
            { name: 'Meril Distributor Compliance Code of Conduct' }
          ]
        }
      })

      // Should show overall progress
      await expect(page.locator('text=1 of 3 completed')).toBeVisible()
      await expect(page.locator('text=33%')).toBeVisible()

      // Should show completed documents
      await expect(page.locator('[data-testid="completed-uploads"]')).toBeVisible()
      await expect(page.locator('text=Distributor Self Declaration')).toBeVisible()
      await expect(page.locator('text=Successfully uploaded')).toBeVisible()
    })
  })

  test.describe('Completion Step', () => {
    test('should display completion summary', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Navigate to completion step
      await page.evaluate(() => {
        window.mockWorkflowState = {
          currentStep: 4,
          uploadedDocuments: [
            { name: 'Policy Adoption Form', upload_datetime: new Date().toISOString() },
            { name: 'Self Declaration', upload_datetime: new Date().toISOString() },
            { name: 'Code of Conduct', upload_datetime: new Date().toISOString() }
          ],
          documentsList: ['Distributor Completion Certificate']
        }
      })

      await page.waitForSelector('[data-testid="completion-step"]')

      // Verify completion message
      await expect(page.locator('text=Process Complete!')).toBeVisible()
      await expect(page.locator('text=All documents have been successfully processed')).toBeVisible()

      // Verify statistics
      await expect(page.locator('text=3')).toBeVisible() // Documents uploaded
      await expect(page.locator('text=100%')).toBeVisible() // Completion rate

      // Verify document list
      await expect(page.locator('text=Policy Adoption Form')).toBeVisible()
      await expect(page.locator('text=Self Declaration')).toBeVisible()
      await expect(page.locator('text=Code of Conduct')).toBeVisible()

      // Verify download options
      await expect(page.locator('button:has-text("Download All Documents")')).toBeVisible()
    })

    test('should handle bulk document download', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="completion-step"]')

      // Mock download APIs
      await page.route('**/api/method/lms.overrides.documents.*', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/pdf',
          body: Buffer.from('Mock PDF content')
        })
      })

      // Click bulk download
      await page.click('button:has-text("Download All Documents")')

      // Verify download process
      await expect(page.locator('text=Downloading All Documents...')).toBeVisible()
      await expect(page.locator('text=All documents sent for download')).toBeVisible()
    })
  })

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Mock API error
      await page.route('**/api/method/lms.overrides.documents.*', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            error: 'Server error occurred'
          })
        })
      })

      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Should display error message
      await expect(page.locator('text=Server error occurred')).toBeVisible()
      await expect(page.locator('button:has-text("Try again")')).toBeVisible()
    })

    test('should handle network connectivity issues', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)

      // Simulate network failure
      await page.route('**/api/method/lms.overrides.documents.*', route => {
        route.abort('failed')
      })

      await page.waitForSelector('[data-testid="upload-step"]')

      // Try to upload a file
      await page.setInputFiles('input[type="file"]', {
        name: 'test.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('test content')
      })

      await page.click('button:has-text("Upload Document")')

      // Should show network error
      await expect(page.locator('text=Upload failed')).toBeVisible()
    })
  })

  test.describe('Accessibility', () => {
    test('should be keyboard navigable', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Test tab navigation
      await page.keyboard.press('Tab')
      await expect(page.locator('button[aria-label="Close modal"]')).toBeFocused()

      await page.keyboard.press('Tab')
      await expect(page.locator('input[id="certification-name"]')).toBeFocused()

      await page.keyboard.press('Tab')
      await expect(page.locator('input[id="certification-date"]')).toBeFocused()
    })

    test('should have proper ARIA labels', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Check ARIA labels
      await expect(page.locator('button[aria-label="Close modal"]')).toBeVisible()
      await expect(page.locator('input[id="certification-name"][required]')).toBeVisible()
    })

    test('should have proper heading structure', async ({ page }) => {
      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Check heading hierarchy
      await expect(page.locator('h2')).toBeVisible() // Modal title
      await expect(page.locator('h3')).toBeVisible() // Step title
      await expect(page.locator('h4')).toBeVisible() // Section titles
    })
  })

  test.describe('Mobile Responsiveness', () => {
    test('should work on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })

      await page.goto(`${baseURL}/lms/courses/${testConfig.courseName}`)
      await page.waitForSelector('[data-testid="document-wizard-modal"]')

      // Modal should be responsive
      await expect(page.locator('[data-testid="document-wizard-modal"]')).toBeVisible()
      await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible()

      // Form elements should be usable
      await page.fill('input[id="certification-name"]', 'John Doe')
      await page.click('button:has-text("I Certify")')

      // Should proceed to next step
      await expect(page.locator('[data-testid="download-step"]')).toBeVisible()
    })
  })
})

test.describe('Distributor Management Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login as system manager
    await page.goto(`${baseURL}/lms`)
    // Assume login process...
  })

  test('should display distributor list', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)

    // Wait for page to load
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Check page title
    await expect(page.locator('h1:has-text("Distributor Management")')).toBeVisible()

    // Check table headers
    await expect(page.locator('th:has-text("Distributor")')).toBeVisible()
    await expect(page.locator('th:has-text("Course")')).toBeVisible()
    await expect(page.locator('th:has-text("Status")')).toBeVisible()
    await expect(page.locator('th:has-text("Progress")')).toBeVisible()
  })

  test('should filter distributors by status', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Select completed status filter
    await page.selectOption('select[data-testid="status-filter"]', 'completed')

    // Should update table
    await expect(page.locator('tbody tr')).toHaveCount(5) // Assuming 5 completed
    await expect(page.locator('text=Completed').first()).toBeVisible()
  })

  test('should search distributors', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Search for specific distributor
    await page.fill('input[data-testid="search-input"]', 'ABC Company')

    // Should filter results
    await expect(page.locator('text=ABC Company')).toBeVisible()
    await expect(page.locator('tbody tr')).toHaveCount(1)
  })

  test('should view distributor details', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Click eye icon to view details
    await page.click('[data-testid="view-distributor-btn"]:first')

    // Should open detail modal
    await expect(page.locator('[data-testid="distributor-detail-modal"]')).toBeVisible()
    await expect(page.locator('text=Distributor Information')).toBeVisible()
    await expect(page.locator('text=Progress Overview')).toBeVisible()
    await expect(page.locator('text=Document Timeline')).toBeVisible()
  })

  test('should download individual distributor documents', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Mock download API
    await page.route('**/api/method/lms.overrides.documents.*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/pdf',
        body: Buffer.from('Mock PDF content')
      })
    })

    // Click download button for first distributor
    await page.click('[data-testid="download-docs-btn"]:first')

    // Should show download progress
    await expect(page.locator('[data-testid="spinner"]')).toBeVisible()
    await expect(page.locator('text=downloaded successfully')).toBeVisible()
  })

  test('should handle bulk operations', async ({ page }) => {
    await page.goto(`${baseURL}/lms/admin/distributor-management`)
    await page.waitForSelector('[data-testid="distributor-table"]')

    // Select multiple distributors
    await page.check('input[type="checkbox"]:first') // Select all checkbox

    // Should show bulk actions
    await expect(page.locator('text=selected')).toBeVisible()
    await expect(page.locator('button:has-text("Bulk Download")')).toBeVisible()

    // Click bulk download
    await page.click('button:has-text("Bulk Download")')

    // Should process bulk download
    await expect(page.locator('text=Starting download')).toBeVisible()
  })
})
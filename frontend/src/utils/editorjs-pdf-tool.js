/**
 * Custom PDF Tool for EditorJS
 * Renders PDFViewerEnhanced component instead of iframe
 */

export default class PDFTool {
  static get isReadOnlySupported() {
    return true
  }

  constructor({ data, config, api, readOnly }) {
    this.data = {
      url: data.url || '',
      caption: data.caption || '',
      height: data.height || '600px',
      ...data
    }
    this.api = api
    this.readOnly = readOnly
    this.wrapper = null
  }

  static get toolbox() {
    return {
      title: 'PDF',
      icon: '<svg width="17" height="15" viewBox="0 0 17 15" xmlns="http://www.w3.org/2000/svg"><path d="M14 4.5V14a2 2 0 01-2 2H4a2 2 0 01-2-2V2a2 2 0 012-2h5.5L14 4.5z"/></svg>'
    }
  }

  render() {
    this.wrapper = document.createElement('div')
    this.wrapper.classList.add('pdf-tool-wrapper')

    if (!this.readOnly) {
      // Edit mode - show input for PDF URL
      const input = document.createElement('input')
      input.classList.add('pdf-url-input')
      input.placeholder = 'Enter PDF URL'
      input.value = this.data.url
      input.addEventListener('input', (e) => {
        this.data.url = e.target.value
        this._updatePreview()
      })
      this.wrapper.appendChild(input)
    }

    // Preview container
    const previewContainer = document.createElement('div')
    previewContainer.classList.add('pdf-preview-container')
    previewContainer.setAttribute('data-pdf-url', this.data.url)
    previewContainer.setAttribute('data-pdf-caption', this.data.caption)
    previewContainer.setAttribute('data-pdf-height', this.data.height)

    if (this.data.url) {
      this._createPreview(previewContainer)
    }

    this.wrapper.appendChild(previewContainer)
    return this.wrapper
  }

  _createPreview(container) {
    container.innerHTML = ''

    if (this.readOnly) {
      // In read-only mode, create a placeholder that will be replaced by Vue component
      const placeholder = document.createElement('div')
      placeholder.classList.add('pdf-viewer-placeholder')
      placeholder.setAttribute('data-pdf-url', this.data.url)
      placeholder.setAttribute('data-pdf-caption', this.data.caption || '')
      placeholder.setAttribute('data-pdf-height', this.data.height || '600px')

      // Add loading message
      placeholder.innerHTML = `
        <div style="padding: 20px; background: #f5f5f5; border-radius: 8px; text-align: center;">
          <div style="margin-bottom: 10px;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div style="font-weight: 500; margin-bottom: 5px;">PDF Document</div>
          <div style="color: #666; font-size: 14px;">${this.data.caption || this.data.url}</div>
        </div>
      `
      container.appendChild(placeholder)
    } else {
      // Edit mode - show simple preview
      const preview = document.createElement('div')
      preview.style.padding = '20px'
      preview.style.background = '#f5f5f5'
      preview.style.borderRadius = '8px'
      preview.style.textAlign = 'center'
      preview.innerHTML = `
        <div>PDF: ${this.data.url}</div>
        ${this.data.caption ? `<div style="margin-top: 10px; color: #666;">${this.data.caption}</div>` : ''}
      `
      container.appendChild(preview)
    }
  }

  _updatePreview() {
    const container = this.wrapper.querySelector('.pdf-preview-container')
    if (container) {
      container.setAttribute('data-pdf-url', this.data.url)
      this._createPreview(container)
    }
  }

  save() {
    return {
      url: this.data.url,
      caption: this.data.caption,
      height: this.data.height
    }
  }

  validate(savedData) {
    if (!savedData.url || !savedData.url.trim()) {
      return false
    }
    return true
  }

  static get pasteConfig() {
    return {
      patterns: {
        pdf: /\.pdf($|\?)/i
      }
    }
  }

  onPaste(event) {
    switch (event.type) {
      case 'pattern':
        const url = event.detail.data
        this.data = {
          url: url,
          caption: '',
          height: '600px'
        }
        this._updatePreview()
        break
    }
  }
}

// Add CSS styles
const style = document.createElement('style')
style.textContent = `
  .pdf-tool-wrapper {
    margin: 20px 0;
  }

  .pdf-url-input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 10px;
    font-size: 14px;
  }

  .pdf-preview-container {
    min-height: 100px;
  }

  .pdf-viewer-placeholder {
    width: 100%;
  }
`

if (typeof document !== 'undefined' && !document.querySelector('#pdf-tool-styles')) {
  style.id = 'pdf-tool-styles'
  document.head.appendChild(style)
}
# Home Assistant Brands Repository Submission

This document outlines the steps needed to add the Emergency Alerts integration to the [Home Assistant Brands repository](https://github.com/home-assistant/brands).

## Why This Is Needed

HACS requires custom integrations to be registered in the brands repository to:
- Provide consistent branding and icons
- Ensure proper UI integration
- Meet HACS validation requirements

## Steps to Add to Brands Repository

### 1. Create Brand Entry

Create a file at `custom_integrations/emergency_alerts/manifest.json` in the brands repository:

```json
{
  "domain": "emergency_alerts",
  "name": "Emergency Alerts",
  "integrations": ["emergency_alerts"],
  "iot_standards": []
}
```

### 2. Add Icons

Add the following icon files to `custom_integrations/emergency_alerts/`:

- `icon.png` - 256x256px icon for the integration
- `logo.png` - Brand logo (optional)

### 3. Icon Requirements

The icon should:
- Be 256x256 pixels
- Use PNG format
- Represent emergency/alert concepts
- Follow Home Assistant design guidelines
- Be clear and recognizable at small sizes

### 4. Suggested Icon Design

For Emergency Alerts, consider an icon featuring:
- Alert/warning symbol (triangle with exclamation)
- Emergency colors (red/orange for urgency)
- Clean, minimalist design
- Good contrast for both light and dark themes

### 5. Submission Process

1. Fork the [home-assistant/brands](https://github.com/home-assistant/brands) repository
2. Create the directory structure: `custom_integrations/emergency_alerts/`
3. Add the `manifest.json` file
4. Add the icon files
5. Submit a pull request with:
   - Clear description of the integration
   - Link to this repository
   - Explanation of the integration's purpose

### 6. Alternative: Ignore Brands Check

If you prefer not to submit to brands immediately, you can ignore this check in HACS validation by adding `brands` to the ignore list in the GitHub Action:

```yaml
- name: HACS validation
  uses: "hacs/action@main"
  with:
    category: "integration"
    ignore: "brands"
```

## Current Status

- ❌ **Not yet submitted** - The integration needs to be added to the brands repository
- 📝 **Ready for submission** - All other HACS requirements are met
- 🎯 **Community adoption** - Consider submitting after gaining users and feedback

## Notes

- The brands repository submission is typically done after an integration has some community adoption
- It's acceptable to ignore the brands check initially during development
- The integration will still work perfectly without brands repository entry
- HACS installation will work, but may show a generic icon 
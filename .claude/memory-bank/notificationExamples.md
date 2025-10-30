# Notification Profile Examples

> **Purpose**: Example notification configurations using Home Assistant's built-in services
> **Date**: 2025-10-29

## Using Built-in Persistent Notifications

Home Assistant includes a persistent notification system that shows in the UI sidebar. Perfect for critical alerts!

### Example 1: Basic Persistent Notification

```yaml
# In alert action configuration
on_triggered:
  - service: persistent_notification.create
    data:
      title: "🚨 Emergency Alert"
      message: "Front door has been open for 5 minutes!"
      notification_id: "emergency_front_door"

on_resolved:
  - service: persistent_notification.dismiss
    data:
      notification_id: "emergency_front_door"
```

### Example 2: Severity-Based Persistent Notifications

```yaml
# Critical severity alert
on_triggered:
  - service: persistent_notification.create
    data:
      title: "🔴 CRITICAL ALERT"
      message: "Water leak detected in basement!"
      notification_id: "water_leak_basement"

on_escalated:
  - service: persistent_notification.create
    data:
      title: "🚨 ESCALATED: Water Leak"
      message: "Water leak has not been acknowledged for 5 minutes!"
      notification_id: "water_leak_escalated"

on_resolved:
  - service: persistent_notification.dismiss
    data:
      notification_id: "water_leak_basement"
  - service: persistent_notification.dismiss
    data:
      notification_id: "water_leak_escalated"
```

### Example 3: With Action Buttons

Home Assistant persistent notifications support action buttons:

```yaml
on_triggered:
  - service: persistent_notification.create
    data:
      title: "⚠️ Security Alert"
      message: "Motion detected in garage while away"
      notification_id: "garage_motion"
      # Note: action buttons require custom handling
```

---

## Mobile App Notifications

If you have the Home Assistant mobile app installed:

### Example 4: Mobile Push Notification

```yaml
on_triggered:
  - service: notify.mobile_app_<your_device>
    data:
      title: "Emergency Alert"
      message: "Front door open while away!"
      data:
        priority: high
        ttl: 0
        channel: Emergency Alerts
        importance: high
        notification_icon: mdi:alert
        tag: "alert_front_door"

on_resolved:
  - service: notify.mobile_app_<your_device>
    data:
      message: "clear_notification"
      data:
        tag: "alert_front_door"
```

### Example 5: Mobile with Action Buttons

```yaml
on_triggered:
  - service: notify.mobile_app_<your_device>
    data:
      title: "🚨 Critical Alert"
      message: "Water leak detected!"
      data:
        priority: high
        ttl: 0
        channel: Emergency Alerts
        actions:
          - action: "ACKNOWLEDGE_ALERT"
            title: "Acknowledge"
          - action: "VIEW_CAMERA"
            title: "View Camera"
        tag: "water_leak"
```

---

## Telegram Integration

### Example 6: Telegram Notification

```yaml
on_triggered:
  - service: notify.telegram
    data:
      title: "🚨 Emergency Alert"
      message: "Front door has been open for 5 minutes while you're away!"

on_escalated:
  - service: notify.telegram
    data:
      title: "⚠️ ESCALATED ALERT"
      message: "Front door alert has not been acknowledged for 5 minutes!"
```

### Example 7: Telegram with Inline Keyboard

```yaml
on_triggered:
  - service: telegram_bot.send_message
    data:
      target: <your_chat_id>
      message: "🚨 Emergency: Front door open!"
      inline_keyboard:
        - "Acknowledge:/acknowledge_alert"
        - "View Camera:/view_front_door"
```

---

## Multi-Channel Escalation Pattern

### Example 8: Progressive Escalation

```yaml
# Level 1: Mobile notification
on_triggered:
  - service: notify.mobile_app_phone
    data:
      title: "Alert: Front Door"
      message: "Door has been open for 5 minutes"

# Level 2: Persistent notification + Mobile
on_acknowledged:
  - service: persistent_notification.create
    data:
      title: "✓ Alert Acknowledged"
      message: "Front door alert acknowledged"
      notification_id: "front_door_ack"

# Level 3: Escalate to Telegram
on_escalated:
  - service: notify.telegram
    data:
      title: "🚨 ESCALATED"
      message: "Front door alert not acknowledged for 5 minutes!"
  - service: persistent_notification.create
    data:
      title: "🚨 ESCALATED ALERT"
      message: "Front door - escalated due to no response"
      notification_id: "front_door_escalated"

# Cleanup
on_resolved:
  - service: persistent_notification.dismiss
    data:
      notification_id: "front_door_ack"
  - service: persistent_notification.dismiss
    data:
      notification_id: "front_door_escalated"
```

---

## Email Notifications

### Example 9: Email Alert

```yaml
on_triggered:
  - service: notify.smtp
    data:
      title: "Emergency Alert: Front Door"
      message: "The front door has been open for 5 minutes while you are away."

on_escalated:
  - service: notify.smtp
    data:
      title: "ESCALATED: Front Door Alert"
      message: "This alert has not been acknowledged for 5 minutes. Please check immediately."
```

---

## Smart Speaker Announcements

### Example 10: Google Home / Alexa Announcement

```yaml
on_triggered:
  # Google Home
  - service: tts.google_translate_say
    data:
      entity_id: media_player.living_room_speaker
      message: "Emergency alert! The front door has been open for 5 minutes!"

  # Or Alexa
  - service: notify.alexa_media
    data:
      target: media_player.bedroom_echo
      message: "Emergency alert! Front door has been open!"
      data:
        type: tts
```

---

## Combining Multiple Notification Types

### Example 11: Kitchen Sink Approach

```yaml
# For critical security alerts - notify EVERYWHERE
on_triggered:
  - service: persistent_notification.create
    data:
      title: "🚨 SECURITY BREACH"
      message: "Back door opened while armed!"
      notification_id: "security_back_door"

  - service: notify.mobile_app_phone
    data:
      title: "🚨 SECURITY BREACH"
      message: "Back door opened while armed!"
      data:
        priority: high
        ttl: 0

  - service: notify.telegram
    data:
      title: "🚨 SECURITY BREACH"
      message: "Back door opened while armed!"

  - service: tts.google_translate_say
    data:
      entity_id: all
      message: "Security alert! Back door has been opened!"

on_acknowledged:
  - service: persistent_notification.create
    data:
      title: "✓ Security Alert Acknowledged"
      message: "Back door alert has been acknowledged"
      notification_id: "security_ack"

on_resolved:
  - service: persistent_notification.dismiss
    data:
      notification_id: "security_back_door"
  - service: persistent_notification.dismiss
    data:
      notification_id: "security_ack"
```

---

## NEW: State-Specific Actions

With the new switch-based architecture, you now have additional action hooks:

### Example 12: Acknowledge Notifications

```yaml
on_acknowledged:
  - service: persistent_notification.create
    data:
      title: "✓ Alert Acknowledged"
      message: "You acknowledged the front door alert"
      notification_id: "front_door_ack"

on_snoozed:
  - service: notify.mobile_app_phone
    data:
      title: "🔕 Alert Snoozed"
      message: "Front door alert snoozed for 5 minutes"

on_resolved:
  - service: persistent_notification.dismiss
    data:
      notification_id: "front_door_main"
  - service: persistent_notification.dismiss
    data:
      notification_id: "front_door_ack"
```

---

## Configuration Tips

### 1. Use Consistent `notification_id`

This allows you to dismiss notifications when alerts are resolved:

```yaml
notification_id: "emergency_<alert_name>"
```

### 2. Severity-Based Channels

For mobile apps, use different channels for different severities:

```yaml
# Critical
data:
  channel: "Emergency - Critical"
  importance: high

# Warning
data:
  channel: "Emergency - Warning"
  importance: default

# Info
data:
  channel: "Emergency - Info"
  importance: low
```

### 3. Tag Mobile Notifications

Use tags to update existing notifications instead of creating new ones:

```yaml
data:
  tag: "alert_<alert_name>"
```

### 4. Test Your Notifications

Create a test alert to verify your notification configuration works:

```yaml
name: "Test Alert"
trigger_type: "template"
template: "{{ false }}"  # Never triggers
severity: "info"
# Your notification config here
```

Then manually trigger it via Developer Tools → Services.

---

## Future: Notification Profiles

In a future update, you'll be able to define notification profiles in Global Settings:

```yaml
# Future feature (not yet implemented)
profiles:
  mobile:
    - service: notify.mobile_app_phone
      data:
        priority: high

  critical:
    - service: notify.mobile_app_phone
    - service: notify.telegram
    - service: persistent_notification.create

  smart_home:
    - service: tts.google_translate_say
      data:
        entity_id: all
```

Then reference them in alerts:

```yaml
on_triggered: use_profile:mobile
on_escalated: use_profile:critical
```

Stay tuned for this feature in a future release!

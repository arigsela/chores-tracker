import { Platform, Alert as RNAlert } from 'react-native';

export interface AlertButton {
  text: string;
  onPress?: (value?: string) => void | Promise<void>;
  style?: 'default' | 'cancel' | 'destructive';
}

export interface PromptButton {
  text: string;
  onPress?: (value?: string) => void | Promise<void>;
  style?: 'default' | 'cancel' | 'destructive';
}

export class Alert {
  static alert(
    title: string,
    message?: string,
    buttons?: AlertButton[]
  ): void {
    if (Platform.OS === 'web') {
      // Web implementation using browser dialogs
      this.webAlert(title, message, buttons);
    } else {
      // Native implementation using React Native Alert
      this.nativeAlert(title, message, buttons);
    }
  }

  static prompt(
    title: string,
    message?: string,
    buttons?: PromptButton[],
    type?: 'default' | 'plain-text' | 'secure-text' | 'login-password',
    defaultValue?: string,
    keyboardType?: string
  ): void {
    if (Platform.OS === 'web') {
      this.webPrompt(title, message, buttons, defaultValue);
    } else {
      this.nativePrompt(title, message, buttons, type, defaultValue, keyboardType);
    }
  }

  private static webAlert(
    title: string,
    message?: string,
    buttons?: AlertButton[]
  ): void {
    const fullMessage = message ? `${title}\n\n${message}` : title;

    if (!buttons || buttons.length === 0) {
      // Simple alert with OK button
      window.alert(fullMessage);
      return;
    }

    if (buttons.length === 1) {
      // Single button - use alert
      window.alert(fullMessage);
      const button = buttons[0];
      if (button.onPress) {
        setTimeout(() => button.onPress!(), 0);
      }
      return;
    }

    // Multiple buttons - use confirm for binary choice
    if (buttons.length === 2) {
      const confirmResult = window.confirm(fullMessage);
      
      // Find cancel and action buttons
      const cancelButton = buttons.find(b => b.style === 'cancel');
      const actionButton = buttons.find(b => b.style !== 'cancel');
      
      if (confirmResult) {
        // User clicked OK - trigger action button
        if (actionButton?.onPress) {
          setTimeout(() => actionButton.onPress!(), 0);
        }
      } else {
        // User clicked Cancel - trigger cancel button
        if (cancelButton?.onPress) {
          setTimeout(() => cancelButton.onPress!(), 0);
        }
      }
      return;
    }

    // More than 2 buttons - use a simple prompt-based solution
    let buttonText = buttons.map((b, i) => `${i + 1}. ${b.text}`).join('\n');
    const choice = window.prompt(`${fullMessage}\n\nChoose an option:\n${buttonText}`, '1');
    
    if (choice) {
      const index = parseInt(choice) - 1;
      if (index >= 0 && index < buttons.length && buttons[index].onPress) {
        setTimeout(() => buttons[index].onPress!(), 0);
      }
    }
  }

  private static nativeAlert(
    title: string,
    message?: string,
    buttons?: AlertButton[]
  ): void {
    const rnButtons = buttons?.map(button => ({
      text: button.text,
      onPress: button.onPress,
      style: button.style,
    }));

    RNAlert.alert(title, message, rnButtons);
  }

  private static webPrompt(
    title: string,
    message?: string,
    buttons?: PromptButton[],
    defaultValue?: string
  ): void {
    const fullMessage = message ? `${title}\n\n${message}` : title;
    const value = window.prompt(fullMessage, defaultValue || '');

    if (!buttons || buttons.length === 0) {
      return;
    }

    if (value !== null) {
      // User entered a value and clicked OK
      const actionButton = buttons.find(b => b.style !== 'cancel') || buttons[0];
      if (actionButton?.onPress) {
        setTimeout(() => actionButton.onPress!(value), 0);
      }
    } else {
      // User clicked Cancel
      const cancelButton = buttons.find(b => b.style === 'cancel');
      if (cancelButton?.onPress) {
        setTimeout(() => cancelButton.onPress!(), 0);
      }
    }
  }

  private static nativePrompt(
    title: string,
    message?: string,
    buttons?: PromptButton[],
    type?: 'default' | 'plain-text' | 'secure-text' | 'login-password',
    defaultValue?: string,
    keyboardType?: string
  ): void {
    const rnButtons = buttons?.map(button => ({
      text: button.text,
      onPress: button.onPress,
      style: button.style,
    }));

    RNAlert.prompt(title, message, rnButtons, type, defaultValue, keyboardType);
  }
}
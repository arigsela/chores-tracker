import React from 'react';
import { Text, StyleSheet, TouchableOpacity, Animated, ActivityIndicator, View } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { colors } from '../../styles/colors';
import { typography } from '../../styles/typography';
import { useScalePress } from '../../hooks/useAnimation';

const AnimatedButton = ({
  title,
  onPress,
  variant = 'primary', // primary, secondary, outline
  size = 'medium', // small, medium, large
  icon,
  iconPosition = 'left',
  disabled = false,
  showLoader = false,
  style,
  textStyle: customTextStyle,
  children,
  ...props
}) => {
  const { scale, onPressIn, onPressOut } = useScalePress();

  const getButtonStyle = () => {
    const baseStyle = [styles.button, styles[`button_${size}`]];
    
    switch (variant) {
      case 'secondary':
        baseStyle.push(styles.buttonSecondary);
        break;
      case 'outline':
        baseStyle.push(styles.buttonOutline);
        break;
      default:
        baseStyle.push(styles.buttonPrimary);
    }

    if (disabled) {
      baseStyle.push(styles.buttonDisabled);
    }

    return baseStyle;
  };

  const getTextStyle = () => {
    const baseStyle = [styles.text, styles[`text_${size}`]];
    
    if (variant === 'outline') {
      baseStyle.push(styles.textOutline);
    } else {
      baseStyle.push(styles.textSolid);
    }

    return baseStyle;
  };

  const textColor = variant === 'outline' ? colors.primary : colors.white;
  const iconSize = size === 'small' ? 16 : size === 'large' ? 24 : 20;

  const renderContent = () => {
    if (showLoader) {
      return <ActivityIndicator color={textColor} size="small" />;
    }

    if (children) {
      return children;
    }

    return (
      <View style={styles.contentContainer}>
        {icon && iconPosition === 'left' && (
          <Icon 
            name={icon} 
            size={iconSize} 
            color={textColor} 
            style={styles.iconLeft}
          />
        )}
        <Text style={[...getTextStyle(), customTextStyle]}>{title}</Text>
        {icon && iconPosition === 'right' && (
          <Icon 
            name={icon} 
            size={iconSize} 
            color={textColor} 
            style={styles.iconRight}
          />
        )}
      </View>
    );
  };

  return (
    <Animated.View style={{ transform: [{ scale }] }}>
      <TouchableOpacity
        style={[...getButtonStyle(), style]}
        onPress={onPress}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        disabled={disabled || showLoader}
        activeOpacity={1}
        {...props}
      >
        {renderContent()}
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
  },
  contentContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  // Size variants
  button_small: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 32,
  },
  button_medium: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    minHeight: 44,
  },
  button_large: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    minHeight: 56,
  },
  // Style variants
  buttonPrimary: {
    backgroundColor: colors.primary,
  },
  buttonSecondary: {
    backgroundColor: colors.secondary,
  },
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.primary,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  // Text styles
  text: {
    fontWeight: '600',
  },
  text_small: {
    ...typography.caption,
  },
  text_medium: {
    ...typography.button,
  },
  text_large: {
    ...typography.button,
    fontSize: 18,
  },
  textSolid: {
    color: colors.white,
  },
  textOutline: {
    color: colors.primary,
  },
  // Icon styles
  iconLeft: {
    marginRight: 8,
  },
  iconRight: {
    marginLeft: 8,
  },
});

export default AnimatedButton;
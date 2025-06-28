import { Platform } from 'react-native';

const fontFamily = Platform.select({
  ios: {
    regular: 'System',
    medium: 'System',
    semibold: 'System',
    bold: 'System',
  },
  android: {
    regular: 'Roboto',
    medium: 'Roboto-Medium',
    semibold: 'Roboto-Medium',
    bold: 'Roboto-Bold',
  },
});

export const typography = {
  // Headers
  h1: {
    fontFamily: fontFamily.bold,
    fontSize: 34,
    lineHeight: 41,
    fontWeight: '700',
  },
  h2: {
    fontFamily: fontFamily.semibold,
    fontSize: 28,
    lineHeight: 34,
    fontWeight: '600',
  },
  h3: {
    fontFamily: fontFamily.semibold,
    fontSize: 22,
    lineHeight: 28,
    fontWeight: '600',
  },
  h4: {
    fontFamily: fontFamily.medium,
    fontSize: 20,
    lineHeight: 25,
    fontWeight: '500',
  },
  
  // Body text
  body: {
    fontFamily: fontFamily.regular,
    fontSize: 17,
    lineHeight: 22,
    fontWeight: '400',
  },
  bodySmall: {
    fontFamily: fontFamily.regular,
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '400',
  },
  
  // Captions
  caption: {
    fontFamily: fontFamily.regular,
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '400',
  },
  
  // Buttons
  button: {
    fontFamily: fontFamily.medium,
    fontSize: 17,
    lineHeight: 22,
    fontWeight: '500',
  },
};

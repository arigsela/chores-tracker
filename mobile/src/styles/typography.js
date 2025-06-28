import { Platform } from 'react-native';

export const typography = {
  // Headers
  h1: {
    fontSize: 32,
    fontWeight: '700',
    lineHeight: 40,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  h2: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  h3: {
    fontSize: 20,
    fontWeight: '600',
    lineHeight: 28,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  
  // Body
  body: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  bodySmall: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  
  // Labels
  label: {
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 20,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  caption: {
    fontSize: 12,
    fontWeight: '400',
    lineHeight: 16,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
  },
  
  // Buttons
  button: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 24,
    fontFamily: Platform.OS === 'ios' ? 'System' : 'Roboto',
    textTransform: 'uppercase',
  },
};
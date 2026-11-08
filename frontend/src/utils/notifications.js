import { toast as hotToast } from 'react-hot-toast';

export const NOTIFICATION_POSITION = 'top-center';

const DURATIONS = {
  success: 3500,
  info: 4500,
  warning: 5000,
  error: 6500,
  loading: Infinity,
};

const BASE_STYLE = {
  background: '#ffffff',
  color: '#1f2937',
  border: '1px solid #e5e7eb',
  borderRadius: '0.75rem',
  boxShadow: '0 10px 25px -5px rgba(15, 23, 42, 0.18)',
  maxWidth: '560px',
  padding: '0.875rem 1rem',
  fontSize: '0.875rem',
  lineHeight: '1.35rem',
};

function optionsFor(type, options = {}) {
  return {
    ...options,
    position: NOTIFICATION_POSITION,
    duration: options.duration === Infinity ? Infinity : DURATIONS[type],
    style: { ...BASE_STYLE, ...(options.style || {}) },
  };
}

const notify = (message, options = {}) => hotToast(
  message,
  optionsFor('info', { icon: 'ℹ️', ...options }),
);

notify.success = (message, options = {}) => hotToast.success(
  message,
  optionsFor('success', options),
);

notify.error = (message, options = {}) => hotToast.error(
  message,
  optionsFor('error', options),
);

notify.info = (message, options = {}) => hotToast(
  message,
  optionsFor('info', { icon: 'ℹ️', ...options }),
);

notify.warning = (message, options = {}) => hotToast(
  message,
  optionsFor('warning', { icon: '⚠️', ...options }),
);

notify.loading = (message, options = {}) => hotToast.loading(
  message,
  optionsFor('loading', options),
);

notify.dismiss = (...args) => hotToast.dismiss(...args);
notify.remove = (...args) => hotToast.remove(...args);
notify.custom = (renderer, options = {}) => hotToast.custom(
  renderer,
  optionsFor('info', options),
);
notify.promise = (promise, messages, options = {}) => hotToast.promise(
  promise,
  messages,
  {
    ...options,
    loading: optionsFor('loading', options.loading),
    success: optionsFor('success', options.success),
    error: optionsFor('error', options.error),
  },
);

export const toast = notify;

export const notificationToasterProps = {
  position: NOTIFICATION_POSITION,
  toastOptions: {
    duration: DURATIONS.info,
    style: BASE_STYLE,
    success: {
      duration: DURATIONS.success,
      iconTheme: { primary: '#10b981', secondary: '#ffffff' },
    },
    error: {
      duration: DURATIONS.error,
      iconTheme: { primary: '#ef4444', secondary: '#ffffff' },
    },
  },
};

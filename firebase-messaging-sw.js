importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyDZb9bdfMFfzBRKM7bMO7GbvIH5CutYZB0",
  authDomain: "cattrade-591fb.firebaseapp.com",
  projectId: "cattrade-591fb",
  storageBucket: "cattrade-591fb.firebasestorage.app",
  messagingSenderId: "168227931827",
  appId: "1:168227931827:web:07fb9c3de0be56395252c6",
  measurementId: "G-F842ZDDB53"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/firebase-logo.png'
  };

  self.registration.showNotification(notificationTitle,
    notificationOptions);
});

const FIREBASE_AUTH_ORIGIN = 'https://k-arp-79th-78team-c140d.firebaseapp.com';

export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (!url.pathname.startsWith('/__/auth/')) {
      return new Response('Not found', { status: 404 });
    }

    const upstreamUrl = new URL(`${url.pathname}${url.search}`, FIREBASE_AUTH_ORIGIN);
    return fetch(new Request(upstreamUrl, request));
  }
};

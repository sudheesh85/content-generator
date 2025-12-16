/** @type {import('next').NextConfig} */
const nextConfig = {
    rewrites: async () => {
        return [
            {
                source: "/api/:path*",
                destination: "http://127.0.0.1:8000/api/:path*",
            },
        ];
    },
    // Note: Next.js rewrites don't support custom timeouts directly
    // The timeout is handled by the fetch request in the frontend (10 minutes)
};

export default nextConfig;

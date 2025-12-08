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
    // Increase timeout for long-running AI operations
    experimental: {
        proxyTimeout: 300000, // 5 minutes
    },
};

export default nextConfig;

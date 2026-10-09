/** @type {import('next').NextConfig} */
// No custom cache headers: reading searchParams (restacks / sort / page) makes
// every route dynamic, and Next sets `no-store` on those, overriding anything
// declared here. An earlier s-maxage header looked effective but did nothing.
export default {};

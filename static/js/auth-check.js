/**
 * Client-side authentication check for protected pages
 * Redirects to login if no valid token is found
 */
(function() {
    // Check if user has a token in localStorage
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        // No token found, redirect to login
        window.location.href = '/login';
        return;
    }
    
    // Optional: Validate token by making a test API call
    // This ensures the token is still valid on the server
    async function validateToken() {
        try {
            const response = await fetch('/api/dashboard/stats', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                // Token is invalid or expired
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_role');
                localStorage.removeItem('user_id');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Token validation error:', error);
            // Don't redirect on network errors, only on auth failures
        }
    }
    
    // Validate token on page load
    validateToken();
})();

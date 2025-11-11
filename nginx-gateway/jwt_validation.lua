local jwt = require "resty.jwt"
local cjson = require "cjson"

-- Get JWT secret from environment or use default
local jwt_secret = os.getenv("JWT_SECRET") or "django-insecure-cxa4o9g=4p#rh+hnx1tn1i=gu#qa+k-vsma^&f4bwf-@gcq+q4"

-- Get Authorization header
local auth_header = ngx.var.http_authorization

if not auth_header then
    ngx.log(ngx.WARN, "Missing Authorization header")
    ngx.status = 401
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode({
        error = "Unauthorized",
        detail = "Missing Authorization header"
    }))
    return ngx.exit(401)
end

-- Extract token from "Bearer <token>"
local token = auth_header:match("Bearer%s+(.+)")
if not token then
    ngx.log(ngx.WARN, "Invalid Authorization header format")
    ngx.status = 401
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode({
        error = "Unauthorized",
        detail = "Token not found or incorrect format. Use: Bearer <token>"
    }))
    return ngx.exit(401)
end

-- Verify JWT
local jwt_obj = jwt:verify(jwt_secret, token)

if not jwt_obj.verified then
    ngx.log(ngx.WARN, "JWT verification failed: ", jwt_obj.reason)
    ngx.status = 401
    ngx.header.content_type = "application/json"
    
    local error_message = "Invalid or expired token"
    if jwt_obj.reason == "verification failed" then
        error_message = "Token signature verification failed"
    elseif jwt_obj.reason == "jwt signature mismatch" then
        error_message = "Token signature mismatch"
    elseif jwt_obj.reason:match("expired") then
        error_message = "Token is invalid or expired"
    end
    
    ngx.say(cjson.encode({
        error = "Unauthorized",
        detail = error_message
    }))
    return ngx.exit(401)
end

-- Check expiration
local exp = jwt_obj.payload.exp
if exp and exp < ngx.time() then
    ngx.log(ngx.WARN, "JWT token expired")
    ngx.status = 401
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode({
        error = "Unauthorized",
        detail = "Token is invalid or expired"
    }))
    return ngx.exit(401)
end

-- Extract user info
-- Your gateway uses 'sub' for user UUID
local user_id = jwt_obj.payload.sub or jwt_obj.payload.user_id or jwt_obj.payload.id
local user_email = jwt_obj.payload.email

if not user_id then
    ngx.log(ngx.WARN, "No user_id found in JWT payload")
    ngx.status = 401
    ngx.header.content_type = "application/json"
    ngx.say(cjson.encode({
        error = "Unauthorized",
        detail = "Invalid token payload"
    }))
    return ngx.exit(401)
end

-- Set variable to pass to upstream (matches your gateway's X-User-Id header)
ngx.var.jwt_user_id = tostring(user_id)

-- Log successful auth
ngx.log(ngx.INFO, "JWT validated for user: ", user_id)

-- Continue to upstream
return
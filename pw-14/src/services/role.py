"""Role-based access control dependencies for FastAPI routes."""

from fastapi import Request, Depends, HTTPException, status

from src.entity.models import Role, User
from src.services.auth import auth_service


class RoleAccess:
    """FastAPI dependency that restricts route access by user role.

    Instances of this class are used as route dependencies. The dependency
    receives the current authenticated user and checks whether the user's role
    is included in the configured list of allowed roles.
    """

    def __init__(self, allowed_roles: list[Role]):
        """Initialize role-based access rules.

        :param allowed_roles: Roles allowed to access the protected route.
        :type allowed_roles: list[Role]
        """
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        """Validate that the current user has one of the allowed roles.

        :param request: Incoming FastAPI request object.
        :type request: Request
        :param user: Current authenticated user resolved from the access token.
        :type user: User
        :raises HTTPException: Raises ``403 Forbidden`` when the user role is
            not allowed for the route.
        :return: ``None`` when access is allowed.
        :rtype: None
        """
        print(request.method, request.url)
        print(f'User role {user.roles}')
        print(f'Allowed roles: {self.allowed_roles}')
        if user.roles not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Operation forbidden')

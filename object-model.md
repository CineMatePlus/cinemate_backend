# Cinemate Application - Object Model

## 1. Overview

Cinemate is a platform that allows users to discover, list, create collections, and interact with movies and TV series. This object model describes the main components of the system and the relationships between them.

## 2. Main Classes

### 2.1. User

The User class represents users registered in the system.

**Properties:**
- **id**: String - Unique user identifier
- **email**: String - User's email address (unique)
- **name**: String - User's name
- **hashed_password**: String - Encrypted user password
- **avatar_url**: String (optional) - Profile picture URL
- **gender**: Enum (FEMALE, MALE, OTHER) - Gender
- **created_at**: DateTime - Account creation date
- **updated_at**: DateTime - Last update date

**Relationships:**
- A user can have multiple collections (1:n)
- A user can make multiple comments (1:n)
- A user can interact with multiple contents (1:n)

### 2.2. Content

The Content class represents movies and TV series in the system.

**Properties:**
- **id**: String - Unique content identifier
- **title**: String - Content title
- **description**: String - Content description
- **genres**: String[] - Content genres (e.g., Comedy, Action)
- **year**: Integer - Production year
- **type**: Boolean - Content type (true: TV Series, false: Movie)
- **image_url**: String (optional) - Poster image URL
- **average_rating**: Float - Average rating (between 0-10)
- **num_likes**: Integer - Number of likes
- **num_watches**: Integer - Number of views
- **num_ratings**: Integer - Number of ratings
- **num_comments**: Integer - Number of comments
- **created_at**: DateTime - Addition date
- **updated_at**: DateTime - Last update date

**Relationships:**
- A content can have multiple comments (1:n)
- A content can have multiple user interactions (1:n)
- A content can be in multiple collections (n:m)

### 2.3. Collection

The Collection class represents content groups created by users.

**Properties:**
- **id**: String - Unique collection identifier
- **title**: String - Collection title
- **is_public**: Boolean - Visibility status (true: Public, false: Private)
- **user_id**: String - ID of the user who created the collection
- **content_ids**: String[] - Content IDs in the collection
- **created_at**: DateTime - Creation date
- **updated_at**: DateTime - Last update date

**Relationships:**
- A collection belongs to one user (n:1)
- A collection can contain multiple contents (n:m)

### 2.4. Comment

The Comment class represents users' comments about contents.

**Properties:**
- **id**: String - Unique comment identifier
- **text**: String - Comment text
- **content_id**: String - ID of the content the comment is made on
- **user_id**: String - ID of the user who made the comment
- **created_at**: DateTime - Creation date
- **updated_at**: DateTime - Last update date

**Relationships:**
- A comment belongs to one user (n:1)
- A comment belongs to one content (n:1)

### 2.5. UserContent Relationship

The UserContent Relationship class represents users' interactions with contents.

**Properties:**
- **id**: String - Unique relationship identifier
- **user_id**: String - User ID
- **content_id**: String - Content ID
- **is_liked**: Boolean - Like status
- **is_watched**: Boolean - Watch status
- **in_watchlist**: Boolean - Addition to watchlist status
- **rated**: Integer (optional) - User rating (between 1-10)
- **last_interacted_at**: DateTime - Last interaction date

**Relationships:**
- A user-content relationship belongs to one user (n:1)
- A user-content relationship belongs to one content (n:1)

## 3. Service Classes

### 3.1. AuthService

Manages user authentication and authorization processes.

**Methods:**
- **register_user()**: Creates a new user registration
- **login_user()**: Logs in a user and generates a token
- **get_user_from_token()**: Extracts user information from a token

### 3.2. ContentService

Performs content management operations.

**Methods:**
- **create_content()**: Creates new content
- **get_content()**: Retrieves content details
- **update_content()**: Updates content information
- **delete_content()**: Deletes content
- **list_contents()**: Lists contents (with filtering support)
- **search_contents()**: Searches in contents

### 3.3. CollectionService

Performs collection management operations.

**Methods:**
- **create_collection()**: Creates a new collection
- **get_collection()**: Retrieves collection details
- **update_collection()**: Updates collection information
- **delete_collection()**: Deletes a collection
- **list_user_collections()**: Lists user's collections
- **add_content_to_collection()**: Adds content to a collection
- **remove_content_from_collection()**: Removes content from a collection

### 3.4. CommentService

Performs comment management operations.

**Methods:**
- **create_comment()**: Creates a new comment
- **get_comment()**: Retrieves comment details
- **update_comment()**: Updates comment content
- **delete_comment()**: Deletes a comment
- **list_content_comments()**: Lists comments made on content

### 3.5. UserContentService

Manages user-content interactions.

**Methods:**
- **like_content()**: Content like operation
- **add_to_watchlist()**: Add to watchlist operation
- **mark_as_watched()**: Mark as watched operation
- **rate_content()**: Content rating operation
- **get_user_content()**: Retrieves user-content relationship details

## 4. Data Flow

The data flow in the Cinemate application is as follows:

1. The user logs into the system through the authentication service and receives a token.
2. This token is used in all API requests and verifies the user's identity.
3. The user can view contents and search through the content service.
4. The user can create and manage personal collections through the collection service.
5. The user can make comments about contents through the comment service.
6. The user can interact with contents through the user-content service (liking, adding to watchlist, rating, etc.).

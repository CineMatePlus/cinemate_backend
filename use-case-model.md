# Cinemate Application - Use Case Model

## 1. Actors

### 1.1. User
Standard user who uses the Cinemate application. They can discover movies and TV series, create collections, comment on content, and leave ratings.

### 1.2. Administrator
User who has the authority to add new content to the system, update content, and delete when necessary.

## 2. Use Cases

### 2.1. User Account Operations

#### 2.1.1. Register
- **Actor:** User
- **Description:** User creates an account to use the application.
- **Preconditions:** User has not registered before.
- **Main Flow:**
  1. User opens the registration form.
  2. Enters name, email, and password information.
  3. Optionally enters gender and avatar information.
  4. Clicks the register button.
  5. System validates the information and registers the user.
- **Alternative Flows:**
  - If the email is already in use, the system displays an error message.
  - If the password does not meet security requirements, the system displays an error message.

#### 2.1.2. Login
- **Actor:** User
- **Description:** Registered user logs into their account.
- **Preconditions:** User has previously registered.
- **Main Flow:**
  1. User opens the login form.
  2. Enters email and password information.
  3. Clicks the login button.
  4. System validates the information and creates a JWT token to log the user in.
- **Alternative Flows:**
  - If email or password is incorrect, the system displays an error message.

#### 2.1.3. Update Profile
- **Actor:** User
- **Description:** User can update their profile information.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User opens the profile page.
  2. Changes the information they want to update.
  3. Clicks the save button.
  4. System updates the information.

### 2.2. Content Operations

#### 2.2.1. List Content
- **Actor:** User, Administrator
- **Description:** Displays a list of movies and TV series in the system.
- **Preconditions:** None
- **Main Flow:**
  1. User opens the content page.
  2. System shows content in a paginated format.
  3. User can use filtering options (genre, year, movie/TV series).

#### 2.2.2. Search Content
- **Actor:** User, Administrator
- **Description:** User can find specific content by searching.
- **Preconditions:** None
- **Main Flow:**
  1. User enters search term in the search field.
  2. System displays relevant content.
  3. User can filter the results.

#### 2.2.3. View Content Details
- **Actor:** User, Administrator
- **Description:** Displays detailed information about content.
- **Preconditions:** None
- **Main Flow:**
  1. User clicks on content from the content list.
  2. System displays the content detail page (title, description, genre, year, rating, comments).

#### 2.2.4. Like Content
- **Actor:** User
- **Description:** User can like content.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User clicks the like button on the content detail page.
  2. System records that the user liked the content.
  3. The content's like count is updated.

#### 2.2.5. Mark Content as Watched
- **Actor:** User
- **Description:** User can indicate that they have watched content.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User clicks the "Watched" button on the content detail page.
  2. System records that the user has watched the content.
  3. The content's view count is updated.

#### 2.2.6. Add Content to Watchlist
- **Actor:** User
- **Description:** User can add content to their watchlist.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User clicks the "Add to Watchlist" button on the content detail page.
  2. System adds the content to the user's watchlist.

#### 2.2.7. Rate Content
- **Actor:** User
- **Description:** User can rate content from 1 to 10.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User uses the rating control on the content detail page.
  2. System saves the user's rating.
  3. The content's average rating is updated.

### 2.3. Collection Operations

#### 2.3.1. Create Collection
- **Actor:** User
- **Description:** User can create personal collections to group content.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User clicks the "New Collection" button on the collections page.
  2. Determines the collection name and visibility setting.
  3. Clicks the create button.
  4. System creates a new collection.

#### 2.3.2. Add Content to Collection
- **Actor:** User
- **Description:** User can add content to a collection.
- **Preconditions:** User is logged in and has created a collection.
- **Main Flow:**
  1. User clicks the "Add to Collection" button on the content detail page.
  2. System lists the user's collections.
  3. User selects the collection they want to add the content to.
  4. System adds the content to the collection.

#### 2.3.3. Remove Content from Collection
- **Actor:** User
- **Description:** User can remove content from a collection.
- **Preconditions:** User is logged in and has content in a collection.
- **Main Flow:**
  1. User clicks the "Remove" button next to the content on the collection detail page.
  2. System removes the content from the collection.

#### 2.3.4. Update Collection
- **Actor:** User
- **Description:** User can update collection information.
- **Preconditions:** User is logged in and has created a collection.
- **Main Flow:**
  1. User clicks the "Edit" button on the collection detail page.
  2. Updates collection information.
  3. Clicks the save button.
  4. System updates the collection information.

#### 2.3.5. Delete Collection
- **Actor:** User
- **Description:** User can delete a collection they created.
- **Preconditions:** User is logged in and has created a collection.
- **Main Flow:**
  1. User clicks the "Delete" button on the collection detail page.
  2. System asks for confirmation of the deletion.
  3. User confirms the deletion.
  4. System deletes the collection.

#### 2.3.6. List Collections
- **Actor:** User
- **Description:** User can list their collections.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User opens the collections page.
  2. System lists the user's collections.

### 2.4. Comment Operations

#### 2.4.1. Add Comment
- **Actor:** User
- **Description:** User can comment on content.
- **Preconditions:** User is logged in.
- **Main Flow:**
  1. User writes their comment in the comment field on the content detail page.
  2. Clicks the send button.
  3. System saves and displays the comment.

#### 2.4.2. Edit Comment
- **Actor:** User
- **Description:** User can edit their own comment.
- **Preconditions:** User is logged in and has made a comment.
- **Main Flow:**
  1. User clicks the "Edit" button next to their comment.
  2. Updates the comment.
  3. Clicks the save button.
  4. System updates the comment.

#### 2.4.3. Delete Comment
- **Actor:** User
- **Description:** User can delete their own comment.
- **Preconditions:** User is logged in and has made a comment.
- **Main Flow:**
  1. User clicks the "Delete" button next to their comment.
  2. System asks for confirmation of the deletion.
  3. User confirms the deletion.
  4. System deletes the comment.

#### 2.4.4. View Content Comments
- **Actor:** User
- **Description:** User can view comments made on content.
- **Preconditions:** None
- **Main Flow:**
  1. User goes to the comments section on the content detail page.
  2. System lists comments made on the content.

### 2.5. Administrator Operations

#### 2.5.1. Add Content
- **Actor:** Administrator
- **Description:** Administrator can add new movies or TV series to the system.
- **Preconditions:** Administrator is logged in.
- **Main Flow:**
  1. Administrator clicks the "Add New Content" button from the content management panel.
  2. Enters content information (title, description, genre, year, image URL, etc.).
  3. Clicks the save button.
  4. System adds the new content.

#### 2.5.2. Update Content
- **Actor:** Administrator
- **Description:** Administrator can update information of existing content.
- **Preconditions:** Administrator is logged in.
- **Main Flow:**
  1. Administrator selects content from the content management panel.
  2. Clicks the "Edit" button.
  3. Updates content information.
  4. Clicks the save button.
  5. System updates the content information.

#### 2.5.3. Delete Content
- **Actor:** Administrator
- **Description:** Administrator can delete content from the system.
- **Preconditions:** Administrator is logged in.
- **Main Flow:**
  1. Administrator selects content from the content management panel.
  2. Clicks the "Delete" button.
  3. System asks for confirmation of the deletion.
  4. Administrator confirms the deletion.
  5. System deletes the content.
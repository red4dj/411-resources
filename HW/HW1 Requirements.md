# 1. Agile

- **Theme:** Get GiggleGit demo into a stable enough alpha to start onboarding some adventurous clients
- **Epic:** Onboarding experience
- **User story 1:** As a vanilla git power-user that has never seen GiggleGit before, I want to quickly identify what parts of GiggleGit are identical to Git and what parts I need to learn.
- **User story 2:** As a team lead onboarding an experienced GiggleGit user, I want to quickly create a new user account and associate it with my organization’s repositories.
- **User story 3:** As a team lead onboarding a new GiggleGit user, I want to quickly share repositories with them and check user permissions.
    - **Task:** Display and edit user permissions.
        - **Ticket 1:** Implement user permissions
            - Implement the ability to securely share repos with specific users and organizations.
        - **Ticket 2:** Easy-to-understand user permission GUI
            - We need a user permission GUI that allows a user to quickly change permissions by user.

### This is not a user story. Why not? What is it?

- *As a user I want to be able to authenticate on a new machine*

This is more of a requirement. It is a specific task the system needs to perform, not a broad way for it to behave.

# 2. Formal requirements

- **Goal:** Conduct a user study to test if users understand what it means to “sync with a snicker”.
- **Non-Goal:** Design a method to sync GiggleGit repos with a snicker.
    - **Non-functional requirement 1:** Variability
        - **Functional requirements:**
            - Have different variants of syncing with a snicker
            - Assign those variants to different users consistently and randomly
    - **Non-functional requirement 2:** Organizability
        - **Functional requirements:**
            - Maintain a list of types and variants of snickering
            - Easily update that list with new knowledge learned from user study
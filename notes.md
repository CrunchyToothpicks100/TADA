### User flow

1. Candidate finishes page 1 off application (email, first_name, last_name, etc.)
      -> If email already exists, prompt user to sign-in to continue, else...
      -> Candidate created (user set to null)
      -> ApplicationToken created
      -> Token emailed as a magic link
      -> Submission and CandidateAnswer updates for every page submitted

2. Candidate clicks magic link
      -> Token validated -> session established
      -> Candidate fills out the rest of the form

3. Candidate submits
      -> Password set and emailed (or they set it themselves)
      -> Token marked used

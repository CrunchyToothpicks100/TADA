### User flow

1. Candidate enters email on application page
      -> auth.User created??? password is non-nullable, so likely not?
      -> Candidate created (email only)
      -> ApplicationToken created
      -> Token emailed as a magic link

2. Candidate clicks link
      -> Token validated -> session established
      -> Candidate fills out the rest of the form (logged in)

3. Candidate submits
      -> Candidate fields populated
      -> CandidateAnswer rows created
      -> Submission created
      -> Password set and emailed (or they set it themselves)
      -> Token marked used

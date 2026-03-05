### User flow

1. Candidate finishes page 1 off application (email, first_name, last_name, etc.)
      -> Candidate created (user set to null)
      -> ApplicationToken created
      -> Token emailed as a magic link
      -> "Lost your progress? Check email for magic link!"
      -> Submission and CandidateAnswer updates for every page submitted

2. Candidate clicks magic link
      -> Token validated -> session established
      -> Candidate fills out the rest of the form

3. Candidate submits
      -> Password set and emailed (or they set it themselves)
      -> Associated tokens deleted

Expiry:
Application token expires in 3 days
If the associated candidate has a NULL user, delete the candidate and cascade the deletion to CandidateAnswer, Submission, etc.

### User flow

Quick definitions:

Non-Candidate - New user, no associated Candidate
Userless Candidate - Candidate that has not finished their first application, user set to null
User Candidate - Candidate that has finished their first application, user associated

1. Non-Candidate finishes page 1 of application (email, first_name, last_name, etc.)
      -> User/Candidate email does not exist 
            -> Userless Candidate created 
            -> ApplicationToken created (expiry details below)
            -> Token emailed as a magic link
            -> Add this to Non-login application page: 
                  -> "Lost your progress? Check email for magic link!"
            -> Submission is generated with candidate_id
            -> Answers are generated for every page submitted
      -> Userless Candidate email exists 
            -> Create new Candidate and token anyways
            -> Any duplicate records get deleted on token expiry, no worries
            -> Candidate continues form
      -> User Candidate email exists 
            -> Continue anyway
            -> Userless Candidate created 
            -> ApplicationToken created
            -> If they're using a faulty email
                  -> They won't be able to authenticate, no User created
            -> If they actually create an entirely new account with the same email
                  -> Alert their dashboard (hey, let's merge your accounts!) 

2. Logged-in User Candidate works on a new application
      -> Skip page 1 (they can update their info on their dashboard)

3. Candidate clicks magic link
      -> Token validated 
            -> session established
            -> token deleted
            -> Candidate fills out the rest of the form
      -> Token invalid -> "Sorry! Your token expired."

4. Candidate submits
      -> Password set and emailed (or they set it themselves)
      -> Associated tokens deleted (VERY IMPORTANT)

Application Token:
      - token CAN ONLY BE USED ONCE
      - token expires in 3 days
      - when token expires, delete the token
      - If the associated candidate has a NULL user, delete the candidate and cascade the deletion to CandidateAnswer, Submission, etc.

Login:
Use phone number or email!

Candidate dashboard:
      - option to change password
      - secure password tips! (add to webpage)
            - use at least 8 characters
            - Do not use the same password you have used with us previously
            - Do not use dictionary words, your name, e-mail address, mobile phone number or other personal information that can be easily obtained.
            - Do not use the same password for multiple online accounts.
      - View applications
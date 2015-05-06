import time
import praw
from random import randint
import ast

#Import username and password.
with open("username_password") as f:
    USERNAME = f.readline()[:-1]
    PASSWORD = f.readline()
f.closed

#Declare WAIT and MAXPOSTS for Reddit.
WAIT = 20
MAXPOSTS = 1000

#Declare subreddit.
sub = "YOUR DESIRED SUBREDDIT"

#Import array of expressions to find and replace.
with open("to_find") as f:
    to_find = ast.literal_eval(f.read())
f.closed

#Define signature.
signatur = "YOUR SIGNATURE"

#Set user agent and login to Reddit.
user_agent = ("YOUR USER AGENT")
r = praw.Reddit(user_agent=user_agent)
r.login(USERNAME, PASSWORD)


#Shorten reply if there is too much space between the replacements.
def shorten_reply(current_element, positions):
    
    positions.sort()
    i = 0
    left_out = 0
        
    while i < len(positions) - 1:
        #Check space between replacements.
        if positions[i+1][0] - positions[i][1] > 120:
            
            #Define start of the cut: Find " " in current_element from end of current replacement + buffer - left_out.
            cut_start = current_element[:positions[i][1] + 50 - left_out].rfind(" ")
            #Define end of the cut: Find " " in current_element from start of next replacement - buffer - left_out. This is 0, so we add end of next replacement - buffer - left_out. 
            cut_end = current_element[positions[i+1][0] - 50 - left_out:].find(" ") + positions[i+1][0] - 49 - left_out
            
            #Cut space out.
            current_element = current_element[:cut_start] + " [...] " + current_element[cut_end:]
            
            #Calculate how much was cut out.
            left_out = left_out + cut_end - cut_start - 7
        
        i += 1
            
    else:
        #Check space from last replacement to end of element.
        if positions[i][1] - left_out - len(current_element) < -120:
            cut_start = positions[i][1] + 50 - left_out
            current_element = current_element[:cut_start] + " [...] "  
    
    return current_element
        

#Check if the author of the element is blacklisted or the element has already been replied to.
def author_check_elements(element, kind):
    author_blacklist = ["Author_1", "Author_2"]
    try:
        print("Checking author of element " + element.id)
        if str(element.author) in author_blacklist:
            print("Skipping element, author is " + str(element.author))
            return True
    except AttributeError:
        element.author = "[DELETED]"
        
    if kind == "posts":
        answers = element.comments
    elif kind == "comments":
        answers = element.replies
    else:
        print("Something went wrong with the answers to the element.")
        
    try:
        for c in answers:
            print("Checking authors of replies to element " + c.id)
            if str(c.author) == USERNAME:
                print("Skipping element, " + str(c.author + " posted in comments"))
                return True
    except(AttributeError):
        c.author = '[DELETED]'


#Main function. Searches for the defined keywords in the fetched comments and replaces them.
def search_comments(elements, kind):
    for element in elements:
        print("Next element: " + element.id)
        if author_check_elements(element, kind):
            continue
        else:
            print("Author of the element and its direct replies are OK. Going on.")
        
        positions = []
        
        #Declare the item which is to be examined as the comment-body or the post's selftext respectively.
        if kind == "posts":
            current_element = element.selftext
        elif kind == "comments":
            current_element = element.body
        else:
            print("Something is wrong with the analyzed element.")
            
        #print("Looking for words.")
        i = 0
        replaced = False
        while i < len(to_find):
            
            key = to_find[i][0]
            
            #Check if there are more then two replacements. If so, choose one randomly.
            if len(to_find[i]) > 2:
                new = to_find[i][randint(1, len(to_find[i]) - 1)]
            else:
                new = to_find[i][1]
            #Search for keywords, replace them, save the position of each replacement.
            while key in current_element.lower():
                pos = current_element.lower().find(key)
                current_element = current_element[:pos] + new + current_element[pos+len(key):]
                replaced = True
                print("Replacing " + key + " with " + new + ".")
                positions.append([pos, pos+len(new)])
            i += 1
        
        #Try to shorten the comment if keywords were found and replaced.
        if replaced == True:
            new_comment = shorten_reply(current_element, positions)
            #Post the edited element as a reply to the original element.
            element.reply("YOUR INTRO " + new_comment + signatur)
        else:
            print("Nothing found in element " + element.id)
        

#Execute everything. Fetch subreddit, extract posts and comments, execute main functions, catch exception, after finishing wait and repeat.
while True:
    print("Fetching subreddit.")
    subreddit = r.get_subreddit(sub)
    subreddit_posts = subreddit.get_new(limit=MAXPOSTS)
    subreddit_comments = subreddit.get_comments(limit=MAXPOSTS)
    
    try:
        kind = "posts"
        print("Checking posts.")
        search_comments(subreddit_posts, kind)
    except Exception as e:
        print("An error has occured while checking posts: " + str(e))

    try:
        kind = "comments"
        print("Checking comments.")
        search_comments(subreddit_comments, kind)
    except Exception as e:
        print("An error has occured while checking comments: " + str(e))

    print("Finished. Starting again in " + str(WAIT) + " seconds.")
    
    time.sleep(WAIT)


#Print final message before the bot stops. 
print("For some reason the robot stopped.")

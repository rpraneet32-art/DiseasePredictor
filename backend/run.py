from app import create_app #imports Factory function create_app from __init__.py
app=create_app() # executes the Factory Function 
if __name__=='__main__':
    app.run(debug=True, port=5000)
    #debug=True helps when server crashes and prints a highly detailed message 
    #checks for changes in code files and restarts server every time we save a change in code files 
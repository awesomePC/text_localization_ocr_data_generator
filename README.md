# text-localization-ocr-data-generator
Text localization OCR data generator

## How to add new Submodule repository in git 

1. In order to add a Git submodule, use the “git submodule add” command and specify the URL of the Git remote repository to be included as a submodule.

2. When adding a Git submodule, your submodule will be staged. As a consequence, you will need to commit your submodule by using the “git commit” command.

    ```
    $ git commit -m "Added the submodule to the project."
    $ git push
    ```

3. To pull a Git submodule, use the “git submodule update” command with the “–init” and the “–recursive” options.
    
    ```console
    $ git submodule update --init --recursive
    ```

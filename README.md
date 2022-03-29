# Text localization OCR data generator & Card Generator

## Introduction

Text localization OCR data generator is a tool for data geneartion, built for the purpose of synthesizing text detection dataset. Diffrent country document ids will be generated using this tool after adding required metadata.

## Preparing and generating card dataset:

1. Select card image to generate data ex. Quatar resident id.
2. Make copy of that card and remove text from that card using [Snap Edit](https://snapedit.app/) or any other text inpaining tool. Download text removed image and Ensure original image and text removed image are of same size.
3. Using PPOCRLabel tool draw cordinates around text to lcoate text, used to identify text location, text height and width for building meta etc. and Manually Write Metadata by refering sample from data folder for now, for this you can refer [video tutorials](https://drive.google.com/drive/u/0/folders/1d2SxJzMOtAVPnXUhYyVQYUcOxZjeWQqj)
4. Generate cards using `python card_generator`

### TODO

- [ ] Add new card layout generator tool
- [x] Improve speed

## How to add new Submodule repository in git 

1. In order to add a Git submodule, use the `git submodule add` command and specify the URL of the Git remote repository to be included as a submodule.

2. When adding a Git submodule, your submodule will be staged. As a consequence, you will need to commit your submodule by using the `git commit` command.

    ```
    $ git commit -m "Added the submodule to the project."
    $ git push
    ```

3. To pull a Git submodule, use the `git submodule update` command with the `–init` and the `–recursive` options.
    
    ```console
    $ git submodule update --init --recursive
    ```

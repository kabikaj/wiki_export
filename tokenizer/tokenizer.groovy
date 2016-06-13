#!/usr/bin/env groovy

/***********************************************************************
 *
 *     tokenizer.groovy  @DEPRECATED
 *
 * Tokenize and segment text received from stdin and yield it to stdout.
 * Tokenization is performed using the java class BreakIterator.
 *
 * The tokenization is performed at the orthographic level, so punctuation
 * is given in separate lines, but clitics are not separated.
 *
 * Input:
 *   Arabic plain text from stdin. The text is expected not to have empty lines
 *   at the beginning or at the end of the file. But there can be empty lines
 *   in the middle.
 *
 * Output:
 *   Json structure containing a list of  each sentence and its tokens:
 *     [ { 'sentence' : str ,
 *         'tokens'   : list ,  # of stings
 *       } ,
 *      ...
 *     ]
 *          
 * Example:
 *   $ cat example_arabic_text | groovy tokenizer.groovy
 * 
 *********************************************************************** */

import java.text.BreakIterator
import java.util.Locale

import groovy.json.JsonOutput


def text = System.in.getText("UTF-8")

/* prepare sentence splitter */
BreakIterator splitSentence = BreakIterator.getSentenceInstance(new Locale("ar","SA"))
splitSentence.setText(text)

/* initialize indexes for sentence boundaries */
int start_S = splitSentence.first()
int end_S = splitSentence.next()

cnt_S = 1

def outjson = []

/* find sentences */
while(end_S != BreakIterator.DONE)
{
    /* get next sentence */
    def sentence = text.substring(start_S, end_S).trim()

    /* prepare token splitter */
    BreakIterator splitToken = BreakIterator.getWordInstance(new Locale("ar","SA"))
    splitToken.setText(sentence)

    /* initialize indexes for token boundaries */
    int start_T = splitToken.first()
    int end_T = splitToken.next()

    def aux = []

    /* find tokens */
    while(end_T != BreakIterator.DONE)
    {
        /* get next token */
        def token = sentence.substring(start_T, end_T).trim()
        
        if(!token.isEmpty())
        {
            aux.add(token)
        }

        /* update token indexes */
        start_T = end_T
        end_T = splitToken.next()
    }

    outjson.add([sentence: sentence, tokens: aux])

    /* update sentence indexes */
    start_S = end_S
    end_S = splitSentence.next()
    cnt_S++
}

def json = JsonOutput.toJson(outjson)
println json.toString()

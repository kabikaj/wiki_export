#!/usr/bin/env groovy

/*     tokenizer.groovy  @DEPRECATED
 * 
 *    Copyright (C) 2016  Alicia González Martínez, aliciagm85+code@gmail.com
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation, either version 3 of the License, or
 *    (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 ***************************************************************************
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
 *   Json structure containing a list of each sentence and its tokens:
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

# CTFd First Blood
A small CTFd plugin to give First Blood points.

This plugin adds a new challenge type that grants additional points to first N people who solve it.

## Installation

Clone this repo to `CTFd/plugins/CTFd_first_blood` in your CTFd installation directory and restart it. You should see the first blood challenge type in new challenge screen.

Tested with CTFd 3.1.1.

## TODO
* Currently, it's not possible to remove solves (or users/teams with solves) that have been granted the additional bonus. I was having a lot of problems getting ondelete=CASCADE to work properly.
* Make sure that bonus points are recalculated when users are shown/hidden, challenge solves are manually removed, scoring settings are updated etc.
* Display who got the bonus on the challenge solves screen

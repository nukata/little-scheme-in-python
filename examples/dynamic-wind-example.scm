;; An implementation of dynamic-wind (originally by Aubrey Jaffer in 1992)
;; and its application to the example code at sec. 6.4 in R5RS
;; cf. https://groups.csail.mit.edu/mac/ftpdir/scheme-mail/HTML/rrrs-1992/msg00194.html
;;     https://schemers.org/Documents/Standards/R5RS/HTML/r5rs-Z-H-9.html#%_sec_6.4

(define *winds* '())

(define dynamic-wind
  (lambda (<thunk1> <thunk2> <thunk3>)
    (<thunk1>)
    (set! *winds* (cons (cons <thunk1> <thunk3>) *winds*))
    ((lambda (ans)
       (set! *winds* (cdr *winds*))
       (<thunk3>)
       ans)
     (<thunk2>))))

(define call/cc
  ((lambda (oldcc)
     (lambda (proc)
       (define winds *winds*)
       (oldcc (lambda (cont)
                (proc (lambda (c2)
                        (_dynamic-do-winds *winds* winds)
                        (cont c2)))))))
   call/cc))

(define _dynamic-do-winds
  (lambda (from to)
    (set! *winds* from)
    (if (not (eq? from to))
        (if (null? from)
            (begin (_dynamic-do-winds from (cdr to))
                   ((car (car to))))
          (if (null? to)
              (begin ((cdr (car from)))
                     (_dynamic-do-winds (cdr from) to))
            (begin ((cdr (car from)))
                   (_dynamic-do-winds (cdr from) (cdr to))
                   ((car (car to)))))))
    (set! *winds* to)))


(define length
  (lambda (lst)
    (if (null? lst)
        0
      (+ 1 (length (cdr lst))))))

(define reverse
  (lambda (lst)
    (define _reverse2
      (lambda (lst result)
        (if (null? lst)
            result
          (_reverse2 (cdr lst) (cons (car lst) result)))))
    (_reverse2 lst '())))

(display
 ((lambda (path c)
    (define add (lambda (s)
                  (set! path (cons s path))))
    (dynamic-wind
      (lambda () (add 'connect))
      (lambda () (add (call/cc
                       (lambda (c0)
                         (set! c c0)
                         'talk1))))
      (lambda () (add 'disconnect)))
    (if (< (length path) 4)
        (c 'talk2)
      (reverse path)))
  '() #f))
(newline)
;; => (connect talk1 disconnect connect talk2 disconnect)

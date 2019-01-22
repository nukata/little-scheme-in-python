;; Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1. 
;; cf. https://oeis.org/A000045
(define fibonacci
  (lambda (n)
    (define _fib
      (lambda (i F_i F_i+1)
        (if (= i n)
            F_i
          (_fib (+ i 1) F_i+1 (+ F_i F_i+1)))))
    (_fib 0 0 1)))                      ; i=0, F(0)=0, F(1)=1

(display (fibonacci 90))
(newline)
;; => 2880067194370816120

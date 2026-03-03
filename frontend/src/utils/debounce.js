export function debounce(fn, delay = 300) {
	let timeoutId = null
	return function (...args) {
		if (timeoutId) {
			clearTimeout(timeoutId)
		}
		timeoutId = setTimeout(() => {
			fn.apply(this, args)
		}, delay)
	}
}
